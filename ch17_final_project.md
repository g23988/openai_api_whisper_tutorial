# Chapter 17. 期末專案：會議逐字稿工具

恭喜，到這章你已經學完整套課的所有技術元件。最後一章我們把它們全部串起來，做一個**真的可以拿出去用**的會議逐字稿工具。

## 專案目標

做一個工具，輸入一份會議錄音（MP3 / MP4 / M4A 等），自動產出：

1. **完整逐字稿**（純文字）
2. **會議摘要**（100 字內）
3. **重點清單**（條列式）
4. **Action Items**（每條含負責人、任務、期限）
5. **匯出格式**：`.txt`（純文字）與 `.md`（Markdown）

支援命令列與 GUI 兩種使用方式。長音檔自動分段。錯誤訊息清楚。可以給沒寫過程式的同事用。

## 整體架構

按照 Chapter 15 的專案結構：

```text
openai-meeting-tool/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py                   # Streamlit GUI 入口
├── meeting_pipeline.py      # 命令列入口
├── src/
│   ├── __init__.py
│   ├── audio.py             # ffmpeg 轉檔與切段
│   ├── transcriber.py       # OpenAI 轉錄
│   ├── summarizer.py        # 摘要 + 結構化會議紀錄
│   └── exporter.py          # 匯出 txt / md
└── uploads/、transcripts/   # 執行時自動建立
```

我們一個檔案一個檔案實作。

## `src/audio.py`：音檔處理

```python
"""音檔轉檔與切段。"""
import json
import subprocess
from pathlib import Path


def get_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_format", "-print_format", "json",
         str(audio_path)],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def prepare(input_path: Path, output_path: Path | None = None) -> Path:
    """轉成 16kHz mono WAV。"""
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_16k.wav")
    if output_path.exists():
        return output_path
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-ac", "1", "-ar", "16000", "-vn",
         "-f", "wav", "-acodec", "pcm_s16le",
         str(output_path)],
        check=True, capture_output=True,
    )
    return output_path


def split(audio_path: Path, work_dir: Path, segment_seconds: int = 600) -> list[Path]:
    """切成多段 WAV。"""
    work_dir.mkdir(parents=True, exist_ok=True)
    pattern = work_dir / "seg_%03d.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(audio_path),
         "-f", "segment", "-segment_time", str(segment_seconds),
         "-reset_timestamps", "1", "-c", "copy",
         str(pattern)],
        check=True, capture_output=True,
    )
    return sorted(work_dir.glob("seg_*.wav"))
```

## `src/transcriber.py`：轉錄

```python
"""OpenAI 轉錄與分段處理。"""
import sys
import time
from pathlib import Path

from openai import OpenAI, APIConnectionError, RateLimitError


def transcribe_one(client: OpenAI, audio_path: Path,
                   model: str = "gpt-4o-transcribe",
                   language: str = "zh") -> str:
    for attempt in range(1, 4):
        try:
            with open(audio_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model=model, file=f, language=language,
                )
            return result.text
        except (APIConnectionError, RateLimitError) as e:
            if attempt == 3:
                raise
            wait = 2 ** attempt
            print(f"  失敗：{e}，{wait}s 後重試...", file=sys.stderr)
            time.sleep(wait)
    return ""


def transcribe_segments(client: OpenAI, segments: list[Path],
                        cache_dir: Path,
                        model: str = "gpt-4o-transcribe",
                        language: str = "zh",
                        progress=None) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    texts = []
    total = len(segments)
    for i, seg in enumerate(segments, start=1):
        cache_file = cache_dir / f"{seg.stem}.txt"
        if cache_file.exists():
            text = cache_file.read_text(encoding="utf-8")
        else:
            if progress:
                progress(i, total, f"轉錄 {seg.name}")
            text = transcribe_one(client, seg, model, language)
            cache_file.write_text(text, encoding="utf-8")
        texts.append(text)
    return "\n\n".join(t.strip() for t in texts if t.strip())
```

## `src/summarizer.py`：摘要與結構化

```python
"""摘要與結構化會議紀錄。"""
from openai import OpenAI
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    owner: str = Field(description="負責人姓名")
    task: str = Field(description="任務內容")
    due_date: str = Field(description="期限，沒提到留空字串")


class MeetingNote(BaseModel):
    title: str = Field(description="會議主題，10 字內")
    summary: str = Field(description="摘要，100 字內")
    key_points: list[str] = Field(description="重點清單")
    action_items: list[ActionItem] = Field(description="行動項清單")


INSTRUCTIONS = """
你會收到一份會議逐字稿。請整理成結構化的會議紀錄。

規則：
1. 標題簡短，反映會議主題
2. 摘要 100 字內，講清楚會議目的與結論
3. 重點清單列出本次討論的關鍵主題（5-8 條）
4. Action items 每條要有：負責人、任務、期限
5. 不要編造資訊，沒提到就留空或空 list
6. 用繁體中文
""".strip()


def summarize_meeting(client: OpenAI, transcript: str,
                      model: str = "gpt-4o") -> MeetingNote:
    response = client.responses.parse(
        model=model,
        instructions=INSTRUCTIONS,
        input=transcript,
        response_format=MeetingNote,
        temperature=0.3,
    )
    return response.output_parsed
```

## `src/exporter.py`：匯出

```python
"""匯出 txt / md。"""
from pathlib import Path
from src.summarizer import MeetingNote


def to_text(transcript: str, note: MeetingNote) -> str:
    lines = [
        f"會議：{note.title}",
        "",
        "摘要：",
        note.summary,
        "",
        "重點：",
    ]
    lines.extend(f"- {p}" for p in note.key_points)
    lines.append("")
    lines.append("Action Items:")
    for a in note.action_items:
        due = f"（{a.due_date}）" if a.due_date else ""
        lines.append(f"- {a.owner}：{a.task}{due}")
    lines.extend(["", "==== 完整逐字稿 ====", "", transcript])
    return "\n".join(lines)


def to_markdown(transcript: str, note: MeetingNote) -> str:
    lines = [
        f"# {note.title}",
        "",
        "## 摘要",
        "",
        note.summary,
        "",
        "## 重點",
        "",
    ]
    lines.extend(f"- {p}" for p in note.key_points)
    lines.extend(["", "## Action Items", ""])
    if note.action_items:
        lines.append("| 負責人 | 任務 | 期限 |")
        lines.append("|---|---|---|")
        for a in note.action_items:
            lines.append(f"| {a.owner} | {a.task} | {a.due_date or '-'} |")
    else:
        lines.append("（無）")
    lines.extend(["", "## 完整逐字稿", "", transcript])
    return "\n".join(lines)


def export(output_dir: Path, base_name: str, transcript: str,
           note: MeetingNote) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_path = output_dir / f"{base_name}.txt"
    md_path = output_dir / f"{base_name}.md"
    txt_path.write_text(to_text(transcript, note), encoding="utf-8")
    md_path.write_text(to_markdown(transcript, note), encoding="utf-8")
    return txt_path, md_path
```

## `meeting_pipeline.py`：命令列入口

```python
"""命令列：完整跑一次。"""
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src import audio, transcriber, summarizer, exporter


def main() -> None:
    parser = argparse.ArgumentParser(description="會議逐字稿工具")
    parser.add_argument("input", help="音檔路徑")
    parser.add_argument("-o", "--output-dir", default="transcripts")
    parser.add_argument("-m", "--transcribe-model",
                        default="gpt-4o-transcribe",
                        choices=["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"])
    parser.add_argument("--summary-model", default="gpt-4o",
                        choices=["gpt-4o", "gpt-4o-mini"])
    parser.add_argument("-s", "--segment-seconds", type=int, default=600)
    args = parser.parse_args()

    load_dotenv()
    client = OpenAI(timeout=60.0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"找不到 {input_path}", file=sys.stderr); sys.exit(1)

    work_dir = input_path.with_suffix(".work")
    cache_dir = work_dir / "cache"

    # 1. 轉檔
    print("[1/4] 轉成 16kHz mono WAV...", file=sys.stderr)
    prepared = audio.prepare(input_path)

    # 2. 切段
    print("[2/4] 切段...", file=sys.stderr)
    segments = audio.split(prepared, work_dir, args.segment_seconds)
    print(f"      {len(segments)} 段", file=sys.stderr)

    # 3. 轉錄
    print("[3/4] 轉錄...", file=sys.stderr)
    def progress(i, total, msg):
        print(f"      [{i}/{total}] {msg}", file=sys.stderr)
    transcript = transcriber.transcribe_segments(
        client, segments, cache_dir,
        model=args.transcribe_model, progress=progress,
    )

    # 4. 摘要 + 結構化
    print("[4/4] 產生會議紀錄...", file=sys.stderr)
    note = summarizer.summarize_meeting(client, transcript, model=args.summary_model)

    # 匯出
    output_dir = Path(args.output_dir)
    txt_path, md_path = exporter.export(
        output_dir, input_path.stem, transcript, note,
    )
    print(f"\n完成。輸出：")
    print(f"  {txt_path}")
    print(f"  {md_path}")


if __name__ == "__main__":
    main()
```

## `app.py`：Streamlit GUI 入口

```python
"""Streamlit GUI：完整工具。"""
import streamlit as st
from pathlib import Path
from openai import OpenAI

from src import audio, transcriber, summarizer, exporter


st.set_page_config(page_title="會議逐字稿工具", layout="wide")
st.title("會議逐字稿工具")

with st.sidebar:
    st.header("設定")
    api_key = st.text_input("OpenAI API Key", type="password",
                            help="只在這次 session 使用，不會儲存")
    transcribe_model = st.selectbox(
        "轉錄模型",
        ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"],
    )
    summary_model = st.selectbox("摘要模型", ["gpt-4o", "gpt-4o-mini"])
    segment_seconds = st.slider("切段秒數", 120, 900, 600, step=60)


uploaded = st.file_uploader(
    "上傳會議錄音（mp3 / mp4 / wav / m4a 等）",
    type=["mp3", "mp4", "m4a", "wav", "webm", "ogg", "flac"],
)

if uploaded and api_key and st.button("開始", type="primary"):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    input_path = upload_dir / uploaded.name
    input_path.write_bytes(uploaded.getbuffer())

    client = OpenAI(api_key=api_key, timeout=60.0)
    work_dir = input_path.with_suffix(".work")
    cache_dir = work_dir / "cache"

    try:
        with st.status("處理中...", expanded=True) as status:
            st.write("轉成 16kHz mono WAV...")
            prepared = audio.prepare(input_path)

            st.write("切段...")
            segments = audio.split(prepared, work_dir, segment_seconds)
            st.write(f"切成 {len(segments)} 段")

            st.write("逐段轉錄...")
            transcript = transcriber.transcribe_segments(
                client, segments, cache_dir,
                model=transcribe_model,
            )

            st.write("產生會議紀錄...")
            note = summarizer.summarize_meeting(client, transcript,
                                                 model=summary_model)

            status.update(label="完成", state="complete", expanded=False)

        # 顯示結果
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader(note.title)
            st.markdown("**摘要**")
            st.write(note.summary)

            st.markdown("**重點**")
            for p in note.key_points:
                st.write(f"- {p}")

            st.markdown("**Action Items**")
            for a in note.action_items:
                due = f"（{a.due_date}）" if a.due_date else ""
                st.write(f"- {a.owner}：{a.task}{due}")

        with col2:
            st.subheader("完整逐字稿")
            st.text_area("", transcript, height=600, label_visibility="collapsed")

        # 下載按鈕
        st.divider()
        txt_content = exporter.to_text(transcript, note)
        md_content = exporter.to_markdown(transcript, note)
        c1, c2 = st.columns(2)
        c1.download_button("下載 .txt", data=txt_content,
                           file_name=f"{input_path.stem}.txt",
                           mime="text/plain")
        c2.download_button("下載 .md", data=md_content,
                           file_name=f"{input_path.stem}.md",
                           mime="text/markdown")
    except Exception as e:
        st.error(f"處理失敗：{type(e).__name__}: {e}")

elif not api_key:
    st.info("請在側邊欄輸入 OpenAI API Key")
```

## README.md

```markdown
# 會議逐字稿工具

把會議錄音變成可讀的逐字稿與會議紀錄。

## 功能

- 上傳 MP3 / WAV / MP4 等格式
- 長音檔自動分段（支援 1 小時以上）
- 自動產生摘要、重點、Action Items
- 匯出 `.txt` 跟 `.md`
- 圖形介面（Streamlit）與命令列兩種模式
- 中途失敗會快取進度，重跑時跳過已完成部分

## 環境需求

- Python 3.10+
- ffmpeg（macOS: `brew install ffmpeg`；Windows: ffmpeg.org）
- OpenAI API key

## 安裝

\`\`\`bash
git clone <your-repo-url>
cd openai-meeting-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入 OPENAI_API_KEY
\`\`\`

## 使用

### GUI

\`\`\`bash
streamlit run app.py
\`\`\`

### 命令列

\`\`\`bash
python meeting_pipeline.py meeting.mp3
python meeting_pipeline.py meeting.mp3 -m gpt-4o-mini-transcribe --summary-model gpt-4o-mini
\`\`\`

## 成本估算

- 1 小時會議：約 $0.4
- 用 `gpt-4o-mini-transcribe` + `gpt-4o-mini`：約 $0.1
- 詳細看 Chapter 16

## 常見問題

**Q：ffmpeg not found**
A：請先用 brew install ffmpeg 或從 ffmpeg.org 下載

**Q：超過 25MB**
A：本工具會自動分段，不會直接打 API。

**Q：跑到一半當掉**
A：再跑一次，已完成的段會跳過。

## 授權

MIT
```

## 評量標準

期末專案完成的標準：

- [ ] 能在本機跑 `python meeting_pipeline.py xxx.mp3` 完整跑完
- [ ] 能在本機跑 `streamlit run app.py` 並完整操作
- [ ] API key 不寫死在程式碼，從 `.env` 或 GUI 輸入
- [ ] 處理失敗會印出清楚錯誤訊息，不只是 Python traceback
- [ ] `.gitignore` 設定正確，`git status` 看不到 `.env` 跟 `.venv/`
- [ ] 有可讀的 README，覆蓋安裝、使用、常見錯誤
- [ ] 至少跑過一個 30 分鐘以上的真實音檔，輸出可讀

## 可以延伸的方向

把這個專案做完後，可以再延伸：

- **多人對話辨識（speaker diarization）**：用 `pyannote.audio` 之類的工具標記「誰在講話」
- **即時轉錄**：用 OpenAI 的 Realtime API，邊講邊轉
- **整合到 Zoom / Google Meet**：自動抓會議錄音，跑完寄 email
- **多語言對齊**：原文 + 翻譯逐字稿並排
- **跑在自己的伺服器**：Streamlit Cloud / Railway / fly.io 部署
- **加上權限管理**：多使用者各自 key、各自空間
- **整合到 Notion / Linear**：自動把 action items 變成 ticket

## 全課回顧

從 Chapter 0 到這裡，我們走過：

- **環境與基礎**（Ch0-2）：終端機、Python 最小子集、檔案與錯誤處理
- **API 概念**（Ch3-4）：什麼是 API、HTTP、JSON
- **第一個工具**（Ch5-8）：環境設定、第一個 API call、Prompt、命令列工具
- **音訊處理**（Ch9-11）：語音轉文字、ffmpeg、長音檔切段
- **產品化**（Ch12-14）：GUI、結構化輸出、Streaming
- **交付**（Ch15-17）：專案結構、安全成本、期末整合

**整套技能其實是「做工具」的工程能力**。模型只是其中一個元件，整個流程從「使用者需求 → 介面 → 處理邏輯 → 模型 → 輸出 → 安全成本」全部都要顧到。

恭喜你完成這套課。現在你會的這套東西，已經可以做出真實有用的小工具。**接下來最重要的事：找一個自己會用、會痛的場景，把它做出來**。聽起來很普通，但這是把「學過」變成「會用」的唯一方式。

## 練習

1. 把這個期末專案完整實作一次，用一場真實的會議錄音跑通流程。
2. 改一個你會用的場景：例如 podcast 字幕、訪談整理、客戶通話分析。看看本架構能不能直接套用、要改哪裡。
3. 把成品丟到 GitHub（記得先檢查 `.gitignore`），寫一份完整 README，給朋友 clone 試用。
4. 估算一個月你會跑多少次、總成本多少。如果有意義，到 OpenAI dashboard 設一個對應的 Monthly budget。
