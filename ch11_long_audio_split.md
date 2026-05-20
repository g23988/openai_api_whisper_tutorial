# Chapter 11. 長音檔切段與轉錄

到目前為止，我們的轉錄工具只能處理小於 25MB 的音檔。但實際情境裡，一場真正的會議錄音很少在這個範圍——一小時 mp3 大概 30 到 60MB。

這章我們解決這個問題：**把長音檔切成多段、各自轉錄、再把結果合併**。聽起來簡單，但有幾個細節決定品質好壞。

## 整體流程

```text
原始音檔
  ↓ ffmpeg 轉成 16kHz mono WAV
  ↓ 計算總時長
  ↓ 決定切段大小
  ↓ ffmpeg 切成多段 WAV
  ↓ 逐段呼叫 OpenAI API 轉錄
  ↓ 合併成一份完整逐字稿
```

每一步我們都已經有零件了。這章把它們串起來。

## 切段策略：為什麼不能簡單切

最天真的做法是「每 5 分鐘切一刀」：

```bash
ffmpeg -i meeting.wav -f segment -segment_time 300 -c copy out_%03d.wav
```

這樣會產生 `out_000.wav`、`out_001.wav`...每段 5 分鐘。**能跑**，但有幾個問題：

1. **切點可能在某人講到一半**——這句話會被斷成兩段，每段都不完整，模型容易誤判
2. **MP3 直接切會出現雜音**——MP3 是有時間結構的壓縮格式，硬切會在切點處產生爆音
3. **沒有重疊**——切點剛好那個字可能在兩段都不完整

**更穩健的做法**：先轉成 WAV（無壓縮）再切；切的時候加 1-2 秒重疊；如果可能，在靜音處切。

> **Tip** — 「在靜音處切」是專業字幕工具（Aegisub、Premiere）的標準做法，叫做 <strong>silence detection</strong>。原理是用 ffmpeg 的 <code>silencedetect</code> filter 掃出所有停頓點，挑距離目標切點最近的停頓做切割。本課為了簡單，我們會用「固定時長 + 重疊」的近似做法，這對會議錄音來說已經夠用。要更嚴謹的，可以看 ffmpeg 的 <code>silencedetect</code> 文件，或者用 <code>pydub</code> 這類 library。

## 決定切段大小

切多大算合適？需要平衡三件事：

1. **每段要小於 25MB**——OpenAI 硬限制
2. **段數不要太多**——每段都是一次 API call，慢且貴
3. **段內上下文要夠**——太短模型沒辦法理解語境

對 16kHz mono WAV 來說：

- **5 分鐘** ≈ 約 10MB，安全進入 25MB 上限
- **10 分鐘** ≈ 約 20MB，接近上限但仍可
- **15 分鐘** ≈ 約 30MB，會爆

**實務上建議 5 到 10 分鐘**。本章範例用 10 分鐘 = 600 秒，加 5 秒重疊。

## 切段：ffmpeg 怎麼做

```python
import subprocess
from pathlib import Path

def split_audio(
    input_path: Path,
    output_dir: Path,
    segment_seconds: int = 600,
    overlap_seconds: int = 5,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / f"{input_path.stem}_%03d.wav"

    # 用 segment muxer：每 (segment_seconds - overlap_seconds) 秒開新檔
    # 但每段都長 segment_seconds 秒，所以前後段有重疊
    step = segment_seconds - overlap_seconds

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-f", "segment",
            "-segment_time", str(segment_seconds),
            "-reset_timestamps", "1",
            "-c", "copy",
            str(output_pattern),
        ],
        check=True, capture_output=True,
    )

    return sorted(output_dir.glob(f"{input_path.stem}_*.wav"))
```

> **Note** — 上面這個寫法為了單純沒做「真正的重疊」——它只是固定 10 分鐘切一刀。要真的有重疊得做兩次 ffmpeg pass 或用 <code>-ss</code> + <code>-t</code> 個別切每一段。對會議錄音這個近似已經夠用：模型對「一段話開頭被切掉前一句」的容忍度其實還不錯。如果你發現切點處有明顯遺漏，再升級到「個別切段、加重疊」的做法。

## 處理每一段

對每個切好的小檔，呼叫 Chapter 9 的轉錄函式：

```python
from openai import OpenAI

client = OpenAI()

def transcribe_segment(audio_path: Path, model: str = "gpt-4o-transcribe") -> str:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=model,
            file=f,
            language="zh",
        )
    return result.text
```

但有幾個增強要做：

**1. 顯示進度**——長音檔可能要跑好幾分鐘：

```python
def transcribe_all(segments: list[Path]) -> list[str]:
    texts = []
    total = len(segments)
    for i, segment in enumerate(segments, start=1):
        print(f"[{i}/{total}] 轉錄 {segment.name}...", file=sys.stderr)
        texts.append(transcribe_segment(segment))
    return texts
```

**2. 失敗重試**——網路或 API 偶爾會抽風：

```python
import time

def transcribe_with_retry(audio_path: Path, max_retries: int = 3) -> str:
    for attempt in range(1, max_retries + 1):
        try:
            return transcribe_segment(audio_path)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            print(f"  失敗：{e}，{wait} 秒後重試...", file=sys.stderr)
            time.sleep(wait)
    return ""
```

`2 ** attempt` 就是 2、4、8 秒的指數退避（exponential backoff）——這是處理網路問題的標準做法。

> **Warning** — 注意 <code>except Exception</code> 在這裡是合理的——重試邏輯本來就要接住「任何網路或 API 錯誤」。但其他地方還是避免 catch-all。實務上更精確的寫法是接 <code>openai.APIError</code>, <code>requests.ConnectionError</code> 等具體類別。

**3. 中途存檔**——如果第 8 段失敗，前 7 段不要白做：

```python
def transcribe_all_safe(segments: list[Path], cache_dir: Path) -> list[str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    texts = []
    for i, segment in enumerate(segments, start=1):
        cache_file = cache_dir / f"segment_{i:03d}.txt"
        if cache_file.exists():
            texts.append(cache_file.read_text(encoding="utf-8"))
            continue

        text = transcribe_with_retry(segment)
        cache_file.write_text(text, encoding="utf-8")
        texts.append(text)
    return texts
```

這樣同一個音檔跑第二次時，已經完成的段會直接跳過。這對「跑到一半當機」「故意暫停換時段」的情境都很有用。

## 合併文字

各段轉錄完，要合併成一份完整逐字稿。最簡單的是直接接起來：

```python
def merge_texts(texts: list[str]) -> str:
    return "\n\n".join(t.strip() for t in texts if t.strip())
```

但如果你之前留了 5 秒重疊，**接點處會有重複句子**。處理重複需要文字比對演算法（例如尋找前段最後一句與後段第一句的重疊），會複雜。本課的近似做法是**用模型來做合併與清理**：

```python
def clean_transcript(raw: str) -> str:
    response = client.responses.create(
        model="gpt-4o-mini",
        instructions=(
            "你會收到一份語音轉錄的逐字稿，可能有：\n"
            "- 接點處的重複句子\n"
            "- 語助詞「呃」「嗯」「就是」過多\n"
            "- 標點不一致\n\n"
            "請整理成乾淨的逐字稿。規則：\n"
            "1. 移除明顯重複的句子\n"
            "2. 適度刪掉過多的語助詞，但保留語氣\n"
            "3. 加上標點符號讓段落清楚\n"
            "4. 不要改變原意，不要編造\n"
            "5. 直接輸出整理結果，不加任何前綴"
        ),
        input=raw,
        temperature=0.2,
    )
    return response.output_text
```

這多花一次 API call（用便宜的 `gpt-4o-mini` 就夠），但結果好讀很多。

## 完整的長音檔轉錄器

把所有零件組起來：

```python
# transcribe_long.py
import argparse
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def prepare_audio(input_path: Path) -> Path:
    output_path = input_path.with_name(f"{input_path.stem}_16k.wav")
    if output_path.exists():
        return output_path
    print(f"轉檔成 16kHz mono WAV...", file=sys.stderr)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-ac", "1", "-ar", "16000", "-vn",
         "-f", "wav", "-acodec", "pcm_s16le",
         str(output_path)],
        check=True, capture_output=True,
    )
    return output_path

def split_audio(input_path: Path, work_dir: Path, segment_seconds: int = 600) -> list[Path]:
    work_dir.mkdir(parents=True, exist_ok=True)
    pattern = work_dir / "seg_%03d.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-f", "segment", "-segment_time", str(segment_seconds),
         "-reset_timestamps", "1", "-c", "copy",
         str(pattern)],
        check=True, capture_output=True,
    )
    return sorted(work_dir.glob("seg_*.wav"))

def transcribe_segment(audio_path: Path, model: str) -> str:
    for attempt in range(1, 4):
        try:
            with open(audio_path, "rb") as f:
                result = client.audio.transcriptions.create(
                    model=model, file=f, language="zh",
                )
            return result.text
        except Exception as e:
            if attempt == 3:
                raise
            print(f"  失敗：{e}，{2**attempt} 秒後重試...", file=sys.stderr)
            time.sleep(2 ** attempt)
    return ""

def main():
    parser = argparse.ArgumentParser(description="長音檔分段轉錄")
    parser.add_argument("input", help="音檔路徑")
    parser.add_argument("-o", "--output", help="逐字稿輸出路徑")
    parser.add_argument("-s", "--segment-seconds", type=int, default=600)
    parser.add_argument("-m", "--model", default="gpt-4o-transcribe")
    args = parser.parse_args()

    input_path = Path(args.input)
    work_dir = input_path.with_suffix(".work")
    cache_dir = work_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".txt")

    prepared = prepare_audio(input_path)
    segments = split_audio(prepared, work_dir, args.segment_seconds)
    print(f"切成 {len(segments)} 段", file=sys.stderr)

    texts = []
    for i, seg in enumerate(segments, start=1):
        cache_file = cache_dir / f"{seg.stem}.txt"
        if cache_file.exists():
            texts.append(cache_file.read_text(encoding="utf-8"))
            print(f"[{i}/{len(segments)}] 跳過（已快取）", file=sys.stderr)
            continue
        print(f"[{i}/{len(segments)}] 轉錄 {seg.name}...", file=sys.stderr)
        text = transcribe_segment(seg, args.model)
        cache_file.write_text(text, encoding="utf-8")
        texts.append(text)

    merged = "\n\n".join(t.strip() for t in texts if t.strip())
    output_path.write_text(merged, encoding="utf-8")
    print(f"逐字稿已輸出到 {output_path}（總長 {len(merged)} 字）")

if __name__ == "__main__":
    main()
```

用法：

```bash
python transcribe_long.py meeting.mp3
python transcribe_long.py meeting.mp3 -s 300   # 改成每段 5 分鐘
python transcribe_long.py meeting.mp3 -m whisper-1
```

## 小結

1. **長音檔不能直接丟 API**——25MB 是硬限制
2. **流程**：轉成 WAV → 切段 → 逐段轉錄 → 合併
3. **切段大小 5 到 10 分鐘**最實用
4. **重試 + 指數退避**處理偶發的 API 失敗
5. **快取每段結果**——失敗時不用全部重跑
6. **合併可以用模型清理**——處理接點重複與語助詞

下一章我們把這個命令列工具加上 GUI，讓不會用終端機的人也能用。

## 練習

1. 找一個你手邊的長音檔（30 分鐘以上），用本章的程式跑完整個流程。
2. 故意把網路斷掉跑一半，然後重連、再跑，確認快取機制有作用、之前完成的段不會重跑。
3. 比較 `gpt-4o-transcribe` 跟 `whisper-1` 在同一個長音檔上的辨識品質與成本。
4. 加上「合併清理」步驟（用 `gpt-4o-mini` 清理重複與語助詞），比較前後差異。
