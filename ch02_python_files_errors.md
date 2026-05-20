# Chapter 2. Python 小白急救包（二）：檔案與錯誤處理

上一章我們學了 Python 的基本語法，但所有範例都活在「記憶體裡」——程式跑完，東西就不見了。這章我們要做兩件事：

1. **把資料寫進檔案、從檔案讀出來**——這樣程式跑完結果還留得住
2. **處理錯誤**——這樣遇到意外狀況（檔案不存在、API 沒回應）程式不會直接崩潰

這兩件事看起來不性感，但**所有實際能用的工具都需要它們**。本課從 Chapter 7 開始做的每一個小工具，都會用到這章學的東西。

## 用 `open()` 讀檔

最基本的讀檔寫法：

```python
file = open("notes.txt", "r", encoding="utf-8")
text = file.read()
file.close()
print(text)
```

這段做了三件事：開啟檔案、讀出全部內容、關閉檔案。`"r"` 代表 "read"（讀取模式），`encoding="utf-8"` 告訴 Python「這個檔案是 UTF-8 編碼」。

但這種寫法有個缺點：**如果中間出錯（檔案壞了、磁碟滿了），`close()` 不會被執行，檔案會一直被佔用**。所以實際寫程式時，我們幾乎都用下面這種寫法。

## `with open()`：永遠正確關閉檔案

```python
with open("notes.txt", "r", encoding="utf-8") as file:
    text = file.read()

print(text)
```

`with` 這個語法叫 **context manager**。它的承諾是：不管裡面的程式碼正常結束、還是中途爆炸，`with` 區塊結束時都會幫你正確收尾——以檔案來說就是自動 `close()`。

> **Tip** — `with` 是 Python 2005 年引入的語法（PEP 343），引入之前所有人都得寫 `try / finally` 手動關檔。發明它的動機很 Pythonic：**正確的寫法應該比錯的寫法還短**。如果忘記關檔很容易出 bug，那就讓「正確關檔」變成更省力的選項。從那之後，「忘記關檔」這個 bug 在 Python 圈基本上絕跡。

寫檔長這樣：

```python
with open("output.txt", "w", encoding="utf-8") as file:
    file.write("Hello, OpenAI\n")
```

`"w"` 代表 "write"（寫入模式），會把檔案內容完全覆蓋掉。如果你想加在尾巴而不是覆蓋，用 `"a"`（append）。

> **Warning** — `"w"` 模式如果遇到既存的檔案，會**毫無提醒地直接覆蓋掉**。寫程式時很容易誤刪重要檔案。建議寫入前先確認目標檔案不存在，或者用版本控制（git）保護重要檔案。

## 編碼：為什麼一定要寫 UTF-8

如果你不寫 `encoding="utf-8"`，Python 會猜——而它在不同平台猜不一樣。macOS 跟 Linux 通常猜 UTF-8，但**Windows 預設是 cp950 或 Big5**（中文版）或 cp1252（英文版）。這代表同一個程式在不同電腦跑出來中文會亂碼。

```python
# 不好的寫法
with open("notes.txt") as f:
    text = f.read()

# 正確的寫法
with open("notes.txt", encoding="utf-8") as f:
    text = f.read()
```

**請養成永遠寫 `encoding="utf-8"` 的習慣**。本課所有範例都會這樣寫。

> **Note** — UTF-8 是當今網際網路 98% 以上內容的編碼方式。它的設計很聰明：英文字母用 1 byte（跟 ASCII 完全相容）、中文用 3 bytes、emoji 用 4 bytes，沒用到的字母不會浪費空間。Big5 跟 cp950 是 1980 年代台灣的中文編碼，現在主要只在 Windows 中文版的「預設值」這種地方還留著——能避就避。

## `Path`：比字串聰明的路徑

到目前為止我們都用字串當路徑：`"notes.txt"`、`"output.txt"`。可以用，但 Python 提供了更好的選擇：`Path`。

```python
from pathlib import Path

input_path = Path("notes.txt")
output_path = Path("results") / "summary.txt"
```

`Path` 比字串多了幾個好處：

```python
input_path.exists()       # 檔案存在嗎？True / False
input_path.suffix         # 副檔名，例如 '.txt'
input_path.stem           # 不含副檔名的檔名，例如 'notes'
input_path.parent         # 上一層資料夾
```

而且 `Path` 用 `/` 串接子路徑，這在三個平台都會自動處理「Windows 是 `\` 但 macOS/Linux 是 `/`」的差異：

```python
data_dir = Path("data")
audio = data_dir / "meeting.mp3"
# macOS/Linux: data/meeting.mp3
# Windows:     data\meeting.mp3
```

讀寫檔案也有更簡潔的寫法：

```python
text = Path("notes.txt").read_text(encoding="utf-8")
Path("output.txt").write_text("Hello", encoding="utf-8")
```

本課從這裡開始，路徑一律用 `Path`，不再用字串。

## try / except：當事情出錯時

到目前為止我們的程式都是「樂觀派」——假設檔案一定存在、API 一定回應、輸入永遠合法。現實當然不是這樣。

```python
from pathlib import Path

text = Path("notes.txt").read_text(encoding="utf-8")
print(text)
```

如果 `notes.txt` 不存在，這段程式會直接崩潰，跳出一大段紅字：

```text
FileNotFoundError: [Errno 2] No such file or directory: 'notes.txt'
```

對使用者來說這毫無幫助。我們要做的是「預期會出錯，並且優雅處理」：

```python
from pathlib import Path

try:
    text = Path("notes.txt").read_text(encoding="utf-8")
    print(text)
except FileNotFoundError:
    print("找不到 notes.txt，請確認檔案是否存在")
```

`try` 區塊裡放「可能出錯的程式」，`except FileNotFoundError` 區塊接住「如果出了這種錯就跑這段」。

可以接住多種錯誤：

```python
try:
    text = Path("notes.txt").read_text(encoding="utf-8")
except FileNotFoundError:
    print("檔案不存在")
except PermissionError:
    print("沒有讀取權限")
```

> **Warning** — 不要寫 <code>except Exception:</code> 或者更糟的 <code>except:</code> 然後什麼都不處理。這會把所有錯誤（包括你的程式 bug）都吃掉，讓你完全看不出哪裡出問題。**永遠精確指定你預期要處理哪些錯誤**。

## `if __name__ == "__main__"`：讓檔案既能執行也能被引用

你會在很多 Python 範例（包括本課之後的所有檔案）看到這個寫法：

```python
def main():
    print("Hello")

if __name__ == "__main__":
    main()
```

這段在做什麼？

Python 檔案有兩種被使用的方式：**直接執行**（`python hello.py`），或者**被另一個檔案匯入**（`from hello import main`）。

當你直接執行檔案，Python 會把 `__name__` 這個內建變數設成 `"__main__"`。但如果這個檔案被別人匯入，`__name__` 會變成檔案名（`"hello"`）。

所以 `if __name__ == "__main__":` 的意思是：「只有當這個檔案是被直接執行的時候，才跑下面這段。」這讓你可以把同一個檔案的函式給別人用，但又不會在別人匯入時意外把你的測試程式也跑一遍。

> **Note** — 這個寫法早期讓很多新手覺得「為什麼要這麼囉嗦」，但它解決了一個很實際的問題：你寫的小工具，未來可能會變成大工具的一部分。一開始就養成這個習慣，到時候不用回頭改。本課後面所有的 `.py` 檔案都會這樣寫。

## 把它湊起來：讀檔、處理、寫檔

我們把這章學的東西組合成一個完整的小程式：讀一個文字檔、計算字數、把結果寫到另一個檔案。

```python
from pathlib import Path

def count_words(text: str) -> int:
    return len(text.split())

def main() -> None:
    input_path = Path("notes.txt")
    output_path = Path("summary.txt")

    try:
        text = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"找不到 {input_path}，請先建立檔案")
        return

    word_count = count_words(text)
    summary = f"檔案 {input_path.name} 有 {word_count} 個字（以空白分隔）"
    output_path.write_text(summary, encoding="utf-8")
    print(summary)

if __name__ == "__main__":
    main()
```

這段把 Ch1 跟 Ch2 學的東西全部用上：函式、型別標註（`text: str`、`-> int`，這只是註解作用，不影響執行）、`Path`、`try / except`、f-string、`if __name__ == "__main__"`。

存成 `wordcount.py`，建立一個 `notes.txt` 隨便打幾個字，跑：

```bash
python3 wordcount.py
```

應該會看到字數，並且產生 `summary.txt`。試試把 `notes.txt` 刪掉再跑一次，看程式有沒有優雅報錯。

## 小結

這章補齊了「寫真正能用的程式」需要的兩塊：

1. **檔案讀寫**：用 `with open(...)` 加 `encoding="utf-8"`，或更現代的 `Path.read_text() / .write_text()`
2. **錯誤處理**：用 `try / except 具體錯誤名稱`，不要 catch-all
3. **`Path`**：跨平台、語意清楚的路徑物件
4. **`if __name__ == "__main__"`**：讓檔案既能執行也能被引用

到這裡，Python 的最小子集學完了。接下來的 Chapter 3 跟 Chapter 4 會回到「概念補課」——什麼是 API、什麼是 HTTP、什麼是 JSON。理解這些，Chapter 5 開始呼叫 OpenAI 才不會像在念咒。

## 練習

1. 建立一個 `notes.txt`，隨便寫幾段中文。用本章的範例算字數，但改成用 `len(text)`（總字元數）而不是 `text.split()`。比較結果差異。
2. 修改範例，讓使用者可以從命令列指定輸入檔名（提示：用 `sys.argv[1]`）。
3. 故意指定一個不存在的檔名跑一次，確認 `try/except` 有接住，程式沒崩潰。
4. 在 `Path` 物件上跑 `.suffix`、`.stem`、`.parent`，觀察它們分別回傳什麼。
