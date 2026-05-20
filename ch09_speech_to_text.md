# Chapter 9. Speech to Text

從這章開始，我們從「文字輸入、文字輸出」進入「音訊輸入、文字輸出」。本課的最終專案是「會議逐字稿工具」，這章是其中最核心的能力：把 MP3 或 WAV 變成文字。

## 為什麼有兩個轉錄模型？

翻開 OpenAI 文件你會發現，能做語音轉文字的模型有兩個：`whisper-1` 跟 `gpt-4o-transcribe`（還有更便宜的 `gpt-4o-mini-transcribe`）。第一次看到的人通常會問：怎麼選？

故事要從 2022 年講起。那年 OpenAI 開源了一個叫做 Whisper 的語音辨識模型，丟到 Hugging Face 上免費讓人下載。它的特色是「多語言、抗噪、長音檔也能處理」，當時很轟動——因為這種品質的模型，以前要付錢給 Google 或 AWS 才用得到。後來 OpenAI 把它包進 API，命名為 `whisper-1`，定價也很低，是這幾年很多會議轉錄、podcast 字幕工具的主力。

到了 2024 年底，OpenAI 把更新一代的多模態能力（也就是 GPT-4o 那一套）也訓練成可以聽音檔，推出了 `gpt-4o-transcribe` 跟更小的 `gpt-4o-mini-transcribe`。這兩個模型的辨識品質比 `whisper-1` 更好，特別是在口音重、背景吵、專有名詞多的情境下差距明顯。但代價是，每分鐘的價格也比較高。

怎麼選？務實的答案是：

- **練習、便宜、量大、品質可接受就好**：用 `whisper-1`
- **正式產品、會議紀錄、要求準確度**：用 `gpt-4o-transcribe`
- **介於兩者之間**：用 `gpt-4o-mini-transcribe`

本章的範例都會用 `gpt-4o-transcribe`，因為這套課的主軸是「做一個能用的會議逐字稿工具」，品質優先。但練習裡我們會故意叫你用 `whisper-1` 跑同一個音檔，親自比較看看，建立自己對「值不值得多付那點錢」的直覺。

## 最簡單的範例

把一個 MP3 轉成文字，需要的程式碼短得驚人：

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

with open("meeting.mp3", "rb") as audio_file:
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
        language="zh",
    )

print(transcription.text)
```

幾個重點：

- **`open(..., "rb")`**：用 binary 模式開啟。音檔是二進位資料，不是文字
- **`client.audio.transcriptions.create()`**：這次不是 `responses.create`，是另一個 endpoint
- **`language="zh"`**：明確告訴模型「這段是中文」，可以省一點 token 並且提升準確度
- **`transcription.text`**：直接拿出辨識結果文字

> **Tip** — 為什麼要寫 <code>language="zh"</code>？模型可以自動偵測，但對中文音檔特別建議手動指定。原因是中英文混雜的情境下（例如會議裡突然冒出英文專有名詞），自動偵測偶爾會「跳」到英文模式，把後面的中文也用英文音標寫出來。明確指定 <code>zh</code> 可以避免這個問題。完整的 language code 看 ISO 639-1（例如英文 <code>en</code>、日文 <code>ja</code>、韓文 <code>ko</code>）。

## 把它變成可重用的函式

跟 Chapter 8 一樣，我們把這個能力包成一個工具：

```python
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def transcribe(
    audio_path: Path,
    model: str = "gpt-4o-transcribe",
    language: str = "zh",
) -> str:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=model,
            file=f,
            language=language,
        )
    return result.text
```

呼叫方式：

```python
text = transcribe(Path("meeting.mp3"))
print(text)
```

## 25MB 的限制

OpenAI 對音檔轉錄有一個重要限制：**單次請求的音檔不能超過 25MB**。

這聽起來很大，但實際上很容易爆。粗略估算：

- **MP3 128kbps**：每分鐘約 1MB → 25 分鐘
- **WAV 44.1kHz stereo**：每分鐘約 10MB → 2.5 分鐘
- **WAV 16kHz mono**：每分鐘約 2MB → 12.5 分鐘

對一場一小時的會議錄音來說，**怎麼處理都會超過 25MB**。這是為什麼下一章我們要學 ffmpeg：用它把音檔壓縮成適合丟進 API 的格式（16kHz mono MP3），然後 Chapter 11 我們會學「分段轉錄」處理超過單檔大小的情況。

> **Warning** — 直接把超過 25MB 的檔案丟進 API，你會得到一個 <code>413 Request Entity Too Large</code> 錯誤。**這個錯誤不會等到處理完才出現，是上傳到一半被中斷**——錢不會花，但時間白費。<strong>所以丟之前先檢查檔案大小</strong>：<code>audio_path.stat().st_size</code> 拿到 byte 數，除以 <code>1024 * 1024</code> 得 MB。

## 支援的音檔格式

API 接受的格式有：

```text
mp3, mp4, mpeg, mpga, m4a, wav, webm, flac, ogg
```

幾乎所有常見的音訊跟影片容器格式都支援。**如果丟影片**（例如 mp4），API 會自動只處理音軌，視覺部分忽略。這對處理錄製會議的 Zoom mp4 很方便。

不支援的格式（例如 wma、ra）就要先用 ffmpeg 轉，下一章會講。

## 加上時間戳記

預設的 `transcription.text` 只是純文字，沒有時間資訊。但會議逐字稿通常希望知道「這句話是第幾分鐘講的」。OpenAI API 支援 `response_format` 參數：

```python
result = client.audio.transcriptions.create(
    model="gpt-4o-transcribe",
    file=f,
    language="zh",
    response_format="verbose_json",
    timestamp_granularities=["segment"],
)
```

`response_format="verbose_json"` 會讓 API 回傳完整的結構化資料，包含每一段的開始時間、結束時間、文字。`timestamp_granularities=["segment"]` 指定要分段時間戳。

回傳的物件用法：

```python
for segment in result.segments:
    start = segment.start
    end = segment.end
    text = segment.text
    print(f"[{start:.1f}s - {end:.1f}s] {text}")
```

> **Note** — <code>gpt-4o-transcribe</code> 跟 <code>whisper-1</code> 對 <code>response_format</code> 與 <code>timestamp_granularities</code> 的支援略有差異——<code>whisper-1</code> 支援字級時間戳（<code>word</code>），<code>gpt-4o-transcribe</code> 在本書寫作當下還只支援段級（<code>segment</code>）。要做字幕（SRT）、字級對齊類工具，目前 <code>whisper-1</code> 比較完整。OpenAI 的功能差異會隨時間變動，呼叫前看一下 [API 文件](https://platform.openai.com/docs/api-reference/audio)。

## 完整範例：命令列轉錄工具

把這章學的東西組合成一個工具 `transcribe.py`：

```python
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

MAX_MB = 25
SUPPORTED_EXTS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".flac", ".ogg"}

def transcribe(audio_path: Path, model: str, language: str) -> str:
    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_MB:
        print(f"錯誤：{audio_path} 是 {size_mb:.1f}MB，超過 {MAX_MB}MB 上限。請先用 ffmpeg 壓縮（見 Chapter 10）。", file=sys.stderr)
        sys.exit(1)

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=model,
            file=f,
            language=language,
        )
    return result.text

def parse_args():
    parser = argparse.ArgumentParser(description="音檔轉文字工具")
    parser.add_argument("input", help="音檔路徑")
    parser.add_argument("-o", "--output", help="輸出 txt 路徑（預設：輸入同名 .txt）")
    parser.add_argument("-m", "--model", default="gpt-4o-transcribe",
                        choices=["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"])
    parser.add_argument("-l", "--language", default="zh")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"錯誤：找不到 {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() not in SUPPORTED_EXTS:
        print(f"錯誤：不支援的格式 {input_path.suffix}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".txt")

    print(f"轉錄中（{args.model}）...", file=sys.stderr)
    text = transcribe(input_path, args.model, args.language)
    output_path.write_text(text, encoding="utf-8")
    print(f"逐字稿已輸出到 {output_path}")

if __name__ == "__main__":
    main()
```

用法：

```bash
python transcribe.py meeting.mp3
python transcribe.py meeting.m4a -m whisper-1 -l en
python transcribe.py meeting.mp3 -o transcript.txt
```

## 小結

1. **兩種主要的轉錄模型**：`whisper-1` 老牌便宜、`gpt-4o-transcribe` 新代品質高
2. **`client.audio.transcriptions.create()`** + `open(file, "rb")` 是基本骨架
3. **`language` 參數要設定**——中文音檔特別有幫助
4. **25MB 是硬限制**——下一章我們會用 ffmpeg 解決
5. **`response_format="verbose_json"`** 拿到段級時間戳，做字幕或會議紀錄會用到

下一章我們深入音訊格式——MP3 vs WAV、取樣率、聲道——並學會用 ffmpeg 把任何音檔壓到適合 API 的大小與品質。

## 練習

1. 找一個你手邊的短 MP3（< 25MB），用本章的程式轉成文字。
2. 同一個音檔用 `whisper-1` 與 `gpt-4o-transcribe` 各跑一次，比較辨識準確度與耗時。
3. 把 `response_format="verbose_json"` 加進去，印出每一段的時間範圍與文字。
4. 故意丟一個 30MB 的 WAV 進去，確認程式有檢查並回報錯誤（不會浪費上傳時間）。
