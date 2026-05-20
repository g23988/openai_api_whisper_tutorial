# Chapter 10. 音訊格式與 ffmpeg 基礎

上一章我們學會把音檔丟進 API 轉成文字。但有個 25MB 的硬限制——一場一小時的會議錄音怎麼樣都會超過。這章我們解決這個問題，順便把「音訊格式」這件事真正講清楚。

## 為什麼語音辨識偏愛 16kHz mono WAV？

等一下我們要用 `ffmpeg` 把音檔轉成 `16kHz mono WAV`。指令長這樣：

```bash
ffmpeg -y -i meeting.mp3 -ac 1 -ar 16000 -vn -f wav -acodec pcm_s16le meeting_16k_mono.wav
```

看起來像咒語。學員的合理疑問是：為什麼是 16kHz？為什麼要 mono？為什麼要 WAV 不繼續用 MP3？這些選擇不是隨便的，背後有具體理由。

**為什麼 16kHz？** 人類講話的能量主要集中在 300Hz 到 3400Hz——這也是傳統電話只取樣到 8kHz 的原因。語音辨識模型通常用 16kHz 訓練，因為這個取樣率剛好涵蓋了人聲的關鍵頻段，又不會像 44.1kHz（CD 品質）那樣帶進一堆對辨識沒幫助的高頻噪音。把音樂用的 44.1kHz 餵給語音模型，模型不會比較準，反而檔案大了快三倍。

**為什麼 mono？** 會議錄音很多時候是雙聲道（左右麥克風或立體聲），但語音辨識只在意「有人在講什麼」，不在意「他坐在你左邊還是右邊」。轉成 mono 把兩個聲道合併，檔案小一半、辨識結果幾乎沒差。如果你的錄音是兩個人各佔一個聲道（例如線上會議的單獨軌錄音），那是另一個問題——你應該分軌轉錄，而不是合成 mono。

**為什麼 WAV 不用 MP3？** MP3 是有損壓縮，為了讓檔案變小，它丟掉了一些人耳不容易察覺的細節。對聽音樂來說沒差，但對模型來說，那些被丟掉的細節有時候正是它判斷子音、尾音的線索。WAV 配 PCM 是未壓縮的原始音訊，給模型最完整的資料。當然 WAV 檔案會大很多——如果你只是要儲存或傳輸，再壓回 MP3 就好。WAV 的角色是「給模型吃的格式」，不是「給人類儲存的格式」。

所以那串指令在做什麼，重講一次就清楚了：把任意音檔轉成「16kHz 取樣、單聲道、未壓縮的 WAV」——這是給語音模型最理想的食物。

> **Note** — 講「給模型最理想的食物」並不表示其他格式不行。OpenAI 的 API 內部其實會幫你做必要的轉換——丟 44.1kHz stereo MP3 也會跑、結果也不會明顯差。差別在**檔案大小**：同一段 1 小時的會議，44.1kHz stereo WAV 可能 600MB，16kHz mono MP3 可能 30MB。後者你還可能直接丟進 25MB API（如果再壓到 64kbps 大概勉強進得去），前者一定爆。所以這章學的不只是「品質優化」，更是「成本與可行性」。

## Container vs Codec

寫這套課最常被問的一個問題：「MP3 跟 WAV 差在哪？」

正確的答案需要先分開兩個概念：

- **Container（容器）**：檔案的「外包裝」，副檔名通常代表它。例如 `.mp3`、`.wav`、`.m4a`、`.ogg`、`.mp4`。
- **Codec（編解碼器）**：實際把聲音壓縮/還原的演算法。例如 MP3 codec、AAC、Opus、PCM、FLAC。

MP3 比較特別——容器跟 codec 同名。但一般情況下兩者可以分開：

- `.wav` 容器裡面通常裝 PCM（未壓縮），但偶爾也裝壓縮資料
- `.m4a` 容器裡面通常是 AAC codec
- `.mp4` 容器裡面可以同時有 AAC 音訊跟 H.264 影像

這個區別在你看 ffmpeg 指令時會清楚很多：`-f wav` 指定容器格式，`-acodec pcm_s16le` 指定音訊 codec。兩個分開設定。

## 用 ffprobe 看音檔有什麼

`ffprobe` 是 ffmpeg 附帶的「音訊偵探」工具，告訴你檔案的真相：

```bash
ffprobe -v error -show_format -show_streams -print_format json meeting.mp3
```

輸出（節錄）：

```json
{
  "streams": [
    {
      "codec_name": "mp3",
      "codec_type": "audio",
      "sample_rate": "44100",
      "channels": 2,
      "bit_rate": "128000",
      "duration": "1832.5"
    }
  ],
  "format": {
    "filename": "meeting.mp3",
    "duration": "1832.5",
    "size": "29320192",
    "bit_rate": "128043"
  }
}
```

可以看到：

- 取樣率 44100 Hz
- 2 聲道（stereo）
- 128 kbps bitrate
- 約 30 分鐘長
- 約 30 MB

這就告訴我們：**這個檔案太大，無法直接丟進 OpenAI API**。但只要轉換取樣率與聲道，可以壓很多。

## 用 ffmpeg 轉成語音辨識友善格式

最常用的指令：

```bash
ffmpeg -y -i meeting.mp3 -ac 1 -ar 16000 -vn -f wav -acodec pcm_s16le meeting_16k_mono.wav
```

把參數拆開：

| 參數 | 意思 |
|---|---|
| `-y` | 覆蓋目標檔案不問 |
| `-i meeting.mp3` | 輸入檔案 |
| `-ac 1` | audio channels = 1（mono） |
| `-ar 16000` | audio rate = 16000 Hz |
| `-vn` | 去掉視訊流（如果輸入是 mp4） |
| `-f wav` | 強制輸出容器格式為 wav |
| `-acodec pcm_s16le` | 音訊 codec 用 16-bit PCM little-endian（最相容的選項） |
| `meeting_16k_mono.wav` | 輸出檔案 |

轉換完用 ffprobe 檢查一下，會看到新檔案是 16kHz mono PCM WAV。

> **Tip** — ffmpeg 的指令以彈性出名，但也以難記出名。一個實用建議：<strong>把常用指令做成 shell 函式或 alias</strong>。例如在你的 <code>~/.zshrc</code> 或 <code>~/.bashrc</code> 加上：<code>function to-asr() { ffmpeg -y -i "$1" -ac 1 -ar 16000 -vn -f wav -acodec pcm_s16le "${1%.*}_16k_mono.wav"; }</code>——以後一行 <code>to-asr meeting.mp3</code> 就搞定。

## 壓縮成更小的 MP3

如果你想保留 MP3 容器但讓檔案變小（例如希望剛好塞進 25MB 限制）：

```bash
ffmpeg -y -i meeting.mp3 -ac 1 -ar 16000 -b:a 64k meeting_small.mp3
```

`-b:a 64k` 指定音訊 bitrate 64 kbps。這對人聲來說品質夠用了，比原本 128 kbps 小一半，又比 WAV 小很多。一小時的會議大約 30MB（如果原本 stereo 44.1k）會壓到 28MB 左右——勉強過 OpenAI 的 25MB 線需要再低一點，例如 `-b:a 48k`。

> **Note** — Bitrate 越低，「壓得越扁」——以人耳來說 64k 已經明顯比 128k 差，但對語音辨識來說 64k 的辨識率掉一點點，48k 開始有感。**不要為了過 25MB 線壓得太兇**——Chapter 11 我們會學「分段」，那是更穩健的解法。

## 在 Python 裡呼叫 ffmpeg

實務上我們不會手動下指令，而是讓 Python 呼叫 ffmpeg。標準做法用 `subprocess`：

```python
import subprocess
from pathlib import Path

def convert_to_asr_friendly(input_path: Path) -> Path:
    output_path = input_path.with_name(f"{input_path.stem}_16k_mono.wav")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-ac", "1",
            "-ar", "16000",
            "-vn",
            "-f", "wav",
            "-acodec", "pcm_s16le",
            str(output_path),
        ],
        check=True,
        capture_output=True,
    )
    return output_path
```

幾個重點：

- 指令用 list 傳，不是字串——避免 shell injection
- `check=True` 讓 ffmpeg 失敗時 Python 也丟 exception
- `capture_output=True` 把 ffmpeg 的輸出抓住，不會弄髒終端機

> **Warning** — <code>subprocess.run</code> 預設不會把 ffmpeg 的詳細錯誤訊息給你。如果遇到失敗，記得 catch <code>subprocess.CalledProcessError</code> 並印出 <code>e.stderr.decode()</code>——ffmpeg 把所有有用的錯誤資訊都印在 stderr。

## 用 ffprobe 拿時長

知道音檔長度對「估算 API 成本」「規劃切段」很重要。`ffprobe` 也能用 Python 呼叫：

```python
import json
import subprocess
from pathlib import Path

def get_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_format", "-print_format", "json",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])
```

呼叫：

```python
duration = get_duration(Path("meeting.mp3"))
print(f"音檔長度：{duration:.1f} 秒（{duration/60:.1f} 分鐘）")
```

## 整合範例：自動準備音檔

把這章的東西組合成一個工具：給定任何音檔，自動轉成 ASR 友善格式，並回報轉換後的大小：

```python
import json
import subprocess
import sys
from pathlib import Path

def get_info(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams",
         "-print_format", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)

def convert(input_path: Path) -> Path:
    output_path = input_path.with_name(f"{input_path.stem}_16k_mono.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-ac", "1", "-ar", "16000", "-vn",
         "-f", "wav", "-acodec", "pcm_s16le",
         str(output_path)],
        check=True, capture_output=True,
    )
    return output_path

def main(input_str: str) -> None:
    input_path = Path(input_str)
    if not input_path.exists():
        print(f"找不到 {input_path}", file=sys.stderr); sys.exit(1)

    info = get_info(input_path)
    before_mb = input_path.stat().st_size / (1024 * 1024)
    duration = float(info["format"]["duration"])
    print(f"原始：{before_mb:.1f} MB, 時長：{duration/60:.1f} 分鐘")

    output_path = convert(input_path)
    after_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"轉換後：{output_path.name}（{after_mb:.1f} MB）")

if __name__ == "__main__":
    main(sys.argv[1])
```

跑：

```bash
python prepare_audio.py meeting.mp3
```

## 小結

1. **Container 跟 Codec 是兩件事**——副檔名通常代表 container，內部可以裝不同 codec
2. **`ffprobe` 看音檔資訊**——時長、取樣率、聲道、bitrate
3. **`ffmpeg` 轉檔**——`-ac 1 -ar 16000` 是語音辨識友善格式的核心兩個參數
4. **語音辨識想要 16kHz mono**——更高品質對辨識無幫助，反而檔案大
5. **Python 用 `subprocess.run` 呼叫 ffmpeg**——指令用 list 傳，`check=True` 抓失敗
6. **`-b:a 64k` 是常用 MP3 bitrate**——對語音辨識來說品質夠

下一章我們解決真正的痛點：一小時的會議錄音怎麼分段送進 API、結果怎麼合併。

## 練習

1. 找一個你手邊的音檔，用 `ffprobe` 看它的資訊（取樣率、聲道、bitrate、時長）。
2. 把這個音檔用 `ffmpeg` 轉成 16kHz mono WAV，比較轉換前後檔案大小。
3. 再轉成 16kHz mono MP3 64kbps，比較三種版本的大小：原始 / WAV / MP3。
4. 寫一個 Python 函式 `audio_summary(path)`，回傳一個 dict 包含：時長（秒）、檔案大小（MB）、取樣率、聲道數。
