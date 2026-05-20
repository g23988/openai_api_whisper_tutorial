# Chapter 8. 做一個文字小工具

到上一章為止，我們的程式都還停留在「在 IDE 裡按執行」的階段。這章我們把它升級成**真正的工具**——一個你可以從終端機呼叫、帶參數、處理檔案、輸出結果的命令列程式。

完成這章之後你會有 `summarize.py`：

```bash
python summarize.py notes.txt --style short --output summary.md
```

這就是一個完整的小工具了。可以放在桌面、可以給同事用、可以排程定時跑。「會用 API」跟「能做出工具」的差別，就在這幾步。

## 任務：文字摘要工具

我們做的工具目標：

- 讀一個文字檔（會議紀錄、文章、信件等）
- 用 OpenAI 產生摘要
- 把摘要寫到另一個檔案
- 支援「短」「中」「長」三種風格
- 命令列指定輸入檔、輸出檔、風格

聽起來功能不少，但有了前面七章的基礎，這只是把零件組裝起來。

## 第一版：寫死的設定

先把最簡單的版本跑起來：

```python
# summarize.py
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

INSTRUCTIONS = """
你是一位專業的中文編輯，專長是把長文章整理成清晰的摘要。

規則：
1. 使用繁體中文
2. 保留所有關鍵資訊與決策
3. 用條列式呈現重點
4. 不評論、不延伸、不加沒講過的資訊
""".strip()

def summarize(text: str) -> str:
    response = client.responses.create(
        model="gpt-4o",
        instructions=INSTRUCTIONS,
        input=text,
        temperature=0.3,
    )
    return response.output_text

if __name__ == "__main__":
    input_path = Path("notes.txt")
    output_path = Path("summary.txt")

    text = input_path.read_text(encoding="utf-8")
    summary = summarize(text)
    output_path.write_text(summary, encoding="utf-8")
    print(f"摘要已輸出到 {output_path}")
```

跑一次：

```bash
python summarize.py
```

能跑了。但「輸入跟輸出檔名寫死」這件事不夠像工具——我們要它能從命令列接參數。

## 加上命令列參數

Python 內建 `argparse` 模組專門處理這件事：

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="文字摘要工具")
    parser.add_argument("input", help="輸入檔案路徑")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="輸出檔案路徑（預設：輸入檔同名 .summary.md）",
    )
    parser.add_argument(
        "-s", "--style",
        choices=["short", "medium", "long"],
        default="medium",
        help="摘要風格（預設：medium）",
    )
    return parser.parse_args()
```

`argparse` 會自動：

- 處理 `--help` 參數，印出說明
- 檢查必填參數有沒有給
- 把 `--style xxx` 轉成 `args.style`
- 出錯時印出清楚的錯誤訊息

> **Tip** — <code>argparse</code> 是 Python 標準庫，能處理 95% 的命令列需求。社群還有更現代的工具像 <code>click</code> 跟 <code>typer</code>，更省事但要多裝一個套件。本課堅持用標準庫——讓學員寫的程式可以在任何乾淨環境跑。

## 加上風格控制

風格的差別由 `instructions` 動態組裝：

```python
STYLE_HINTS = {
    "short": "用 3 個條列，每條不超過 30 字。",
    "medium": "用 5 到 8 個條列，每條約 50 字。",
    "long": "用條列加段落混合，完整保留所有重點與細節。",
}

def build_instructions(style: str) -> str:
    return f"""
你是一位專業的中文編輯，專長是把長文章整理成清晰的摘要。

規則：
1. 使用繁體中文
2. 保留所有關鍵資訊與決策
3. {STYLE_HINTS[style]}
4. 不評論、不延伸、不加沒講過的資訊
""".strip()
```

這就是「把 prompt 模板化」最簡單的做法——準備幾個變化版本，用 f-string 拼起來。

## 處理錯誤

實際工具會遇到的錯誤：

- 輸入檔不存在
- 輸入檔讀不到（權限、編碼）
- 輸入是空的
- 網路斷線、API key 過期
- 模型回了空字串

不需要每種都處理得很完美，但**最常見的幾種要接住，給使用者看得懂的訊息**：

```python
def read_input(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"錯誤：{path} 不是 UTF-8 編碼", file=sys.stderr)
        sys.exit(1)

    if not text.strip():
        print(f"錯誤：{path} 是空檔案", file=sys.stderr)
        sys.exit(1)

    return text
```

> **Note** — <code>sys.stderr</code> 是「錯誤訊息的標準輸出通道」，跟一般 <code>print()</code> 用的 <code>stdout</code> 分開。這在實務上很有用——使用者可以做 <code>python summarize.py input.txt &gt; output.txt</code>，正常輸出會寫進 <code>output.txt</code>，錯誤訊息會留在螢幕上。<code>sys.exit(1)</code> 則告訴外面的程式「我失敗了」（0 是成功、非 0 是失敗），這在腳本串接時很重要。

## 把所有東西組起來

完整的 `summarize.py`：

```python
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

STYLE_HINTS = {
    "short": "用 3 個條列，每條不超過 30 字。",
    "medium": "用 5 到 8 個條列，每條約 50 字。",
    "long": "用條列加段落混合，完整保留所有重點與細節。",
}

def build_instructions(style: str) -> str:
    return f"""
你是一位專業的中文編輯，專長是把長文章整理成清晰的摘要。

規則：
1. 使用繁體中文
2. 保留所有關鍵資訊與決策
3. {STYLE_HINTS[style]}
4. 不評論、不延伸、不加沒講過的資訊
""".strip()

def summarize(text: str, style: str) -> str:
    response = client.responses.create(
        model="gpt-4o",
        instructions=build_instructions(style),
        input=text,
        temperature=0.3,
    )
    return response.output_text

def read_input(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {path}", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"錯誤：{path} 不是 UTF-8 編碼", file=sys.stderr)
        sys.exit(1)

    if not text.strip():
        print(f"錯誤：{path} 是空檔案", file=sys.stderr)
        sys.exit(1)

    return text

def parse_args():
    parser = argparse.ArgumentParser(description="文字摘要工具")
    parser.add_argument("input", help="輸入檔案路徑")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="輸出檔案路徑（預設：輸入檔同名 .summary.md）",
    )
    parser.add_argument(
        "-s", "--style",
        choices=["short", "medium", "long"],
        default="medium",
        help="摘要風格（預設：medium）",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix(".summary.md")

    text = read_input(input_path)
    print(f"正在處理 {input_path}（{len(text)} 字）...", file=sys.stderr)

    summary = summarize(text, args.style)
    output_path.write_text(summary, encoding="utf-8")
    print(f"摘要已輸出到 {output_path}")

if __name__ == "__main__":
    main()
```

用法：

```bash
python summarize.py notes.txt
python summarize.py notes.txt --style short
python summarize.py notes.txt -s long -o final.md
python summarize.py --help
```

`--help` 會自動印出 argparse 幫你產生的說明，包括所有參數、預設值、選項。

## 對檔案大小要小心

你可能會想：「我把整本 30 萬字的小說丟進去摘要不就好了？」

別這樣。原因：

1. **模型有 context window 上限**——`gpt-4o` 大約 128k tokens（約 10 萬中文字），超過會 truncate 或報錯
2. **單次呼叫越長，越貴**——成本跟 token 數成正比
3. **長文摘要品質會下降**——模型對「文件中間」的記憶比較弱

> **Warning** — 對於可能超過模型 context window 的長文件，**不要把整份丟進去**。本課 Chapter 11 會教「分段處理」的模式——把文件切成小段、各自摘要、再合併。同樣的思路會用在 Chapter 11 的長音檔轉錄。

對本章的工具，建議在 `read_input()` 加個檢查：

```python
MAX_CHARS = 50000  # 約 5 萬中文字，安全範圍

if len(text) > MAX_CHARS:
    print(f"錯誤：檔案太大（{len(text)} 字），請先分段。", file=sys.stderr)
    sys.exit(1)
```

## 小結

這章把 API 呼叫從「在編輯器按執行」進化成「真正能用的命令列工具」：

1. **`argparse`** 處理命令列參數，含 `--help`
2. **`Path.with_suffix()`** 自動產生輸出檔名
3. **錯誤處理**用 `sys.stderr` 跟 `sys.exit(1)`，配合 shell 慣例
4. **Prompt 模板化**：用 dict + f-string 切換風格
5. **檔案大小檢查**：避免不小心把太大檔案丟進去

下一章我們轉換主題，從文字進入**音訊**——學怎麼把 MP3 / WAV 轉成文字。

## 練習

1. 跑一次 `python summarize.py --help`，看 argparse 自動產生的說明。
2. 加一個 `--language` 參數，可選 `zh`、`en`、`ja`，並在 instructions 反映。
3. 加一個 `--model` 參數，可選 `gpt-4o`、`gpt-4o-mini`，比較兩者輸出品質與你會用哪個。
4. 改寫成「批次模式」：給定一個資料夾，自動對裡面所有 `.txt` 檔做摘要。（提示：`Path("docs").glob("*.txt")`）
