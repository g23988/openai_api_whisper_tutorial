# Chapter 1. Python 小白急救包（一）：語法與資料

這章不是教完整的 Python。完整的 Python 教一本書、一學期、甚至一個職涯都教不完。我們只挑一個最小的子集：剛好夠讀懂本課所有範例的那幾個語法。

學完這章你不會變成 Python 工程師。但你會看懂後面所有的程式碼在做什麼，這對「使用 API」來說已經足夠。剩下的細節，等你做完幾個小工具、開始想自己改造範例的時候，自然會學到。

## 寫程式之前：怎麼跑 Python

最快的方式是打開終端機，直接打：

```bash
python3
```

你會看到三個 `>>>` 符號，這叫 REPL（Read-Eval-Print Loop），可以一行一行試 Python。要離開的話打 `exit()` 或按 `Ctrl + D`。

但本課大部分時候我們會把程式存成 `.py` 檔案，然後執行：

```bash
python3 hello.py
```

兩種方式我們都會用。REPL 適合快速試一行，檔案適合寫真正的工具。

## 變數與字串

變數是給一個值取個名字，方便之後重複使用：

```python
name = "OpenAI"
year = 2025
```

Python 不需要事先宣告型別——你給它什麼，它就記住什麼。`name` 是字串（一串文字），`year` 是整數。

字串可以用雙引號 `"..."` 或單引號 `'...'`，兩個一模一樣：

```python
greeting = "Hello"
greeting = 'Hello'
```

> **Note** — 為什麼有兩種寫法？因為當字串本身包含引號時你需要另一種包它。例如 <code>"It's a test"</code> 用雙引號包，這樣裡面的單引號就不會搞混。其他語言（像 Java、C#）只有雙引號，遇到這種情況得用 <code>\'</code> 跳脫，比較囉嗦。

把字串接起來用 `+`：

```python
full = "Hello" + " " + "OpenAI"
print(full)  # Hello OpenAI
```

或者用 f-string（formatted string）把變數塞進去，這是現代 Python 最常用的寫法：

```python
name = "OpenAI"
year = 2025
print(f"{name} 在 {year} 年很紅")
# OpenAI 在 2025 年很紅
```

f-string 就是「字串前面加個 f」，然後用 `{}` 包住變數。本課所有要組合文字的地方幾乎都用這個。

## list：有順序的清單

`list` 是一串有順序的東西，用方括號 `[]` 包起來：

```python
models = ["gpt-4o", "gpt-4o-mini", "whisper-1"]
```

存取用索引（從 0 開始）：

```python
print(models[0])  # gpt-4o
print(models[2])  # whisper-1
```

> **Tip** — 「從 0 開始」是程式語言的傳統，原因是早期硬體用「記憶體偏移量」做索引——第一個元素的偏移量是 0，第二個是 1，以此類推。現代程式語言大多沿用，雖然有少數例外（Lua、R、MATLAB 從 1 開始）。一開始很彆扭，習慣之後反而會覺得從 1 開始的設計很怪。

加新東西到尾巴：

```python
models.append("o1")
print(models)  # ['gpt-4o', 'gpt-4o-mini', 'whisper-1', 'o1']
```

算長度：

```python
print(len(models))  # 4
```

## dict：用名字查資料

`dict`（dictionary）是「鍵值對」的集合，用大括號 `{}` 包起來：

```python
pricing = {
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "whisper-1": 0.006,
}
```

存取用 key：

```python
print(pricing["gpt-4o"])  # 2.50
```

加或改值：

```python
pricing["o1"] = 15.00
```

`list` 跟 `dict` 是 Python 裡最常用的兩種容器。粗略的判斷方式是：**有順序、會依序處理的，用 list；要用名字查的，用 dict**。本課之後處理 API 回傳資料、設定檔、結構化輸出，幾乎都是這兩個的組合。

> **Note** — 講白話一點，OpenAI API 回傳給你的 JSON 物件，在 Python 裡面就是一個 dict 套 list 套 dict 的結構。看懂這兩個容器，你才看得懂 API 回傳的東西長什麼樣。Chapter 4 會詳細講 JSON。

## if：根據狀況做不同的事

```python
score = 85

if score >= 90:
    print("優")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

幾個重點：

- 條件後面要加冒號 `:`
- 條件成立要執行的程式碼**往內縮排**（通常是 4 個空格）
- `elif` 是 "else if" 的縮寫
- 結尾不需要分號或大括號

縮排這件事下面會專門講。

## for：對一群東西做同樣的事

```python
models = ["gpt-4o", "gpt-4o-mini", "whisper-1"]

for model in models:
    print(f"模型：{model}")
```

`for X in Y` 的意思是「把 Y 裡面的每個東西，依序取出來叫做 X」。執行結果：

```text
模型：gpt-4o
模型：gpt-4o-mini
模型：whisper-1
```

對 `dict` 做迴圈預設會拿到 key：

```python
for name in pricing:
    print(name, pricing[name])
```

但通常我們會用 `.items()` 同時拿 key 跟 value：

```python
for name, price in pricing.items():
    print(f"{name} 每百萬 token {price} 美金")
```

## 函式：把一段操作打包

如果同一段邏輯要重複用，包成函式：

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("OpenAI"))   # Hello, OpenAI!
print(greet("學員"))     # Hello, 學員!
```

幾個重點：

- `def` 是定義函式的關鍵字
- 函式名後面是參數，用括號包起來
- `return` 把結果交還給呼叫的人
- 函式內容也是縮排

如果不需要回傳值（例如函式只負責印東西），可以省略 `return`：

```python
def print_models(models):
    for model in models:
        print(f"- {model}")

print_models(["gpt-4o", "o1"])
```

## 縮排：Python 最大的脾氣

如果你以前寫過 Java、JavaScript、C++，會習慣用大括號 `{}` 標示「這幾行是一組」。Python 不用大括號——它用**縮排**：

```python
if True:
    print("這行是 if 的內容")
    print("這行也是 if 的內容")
print("這行不是 if 的內容")
```

縮排相同數量空格的程式碼算一組。縮排不對，程式直接跑不動，會跳 `IndentationError`。

> **Warning** — 千萬不要 Tab 跟空格混用。Python 3 會直接報錯。本課推薦你的編輯器（VS Code、PyCharm）一律設定「Tab 自動展開成 4 個空格」。一旦設好，按 Tab 就會出 4 個空格，永遠不會混。

這個設計剛開始很煩，但故事其實滿有趣的。

> **Tip** — Python 是 1989 年由 Guido van Rossum 在荷蘭設計的。他之前在另一個語言 ABC 工作過，那個語言就是用縮排來組程式碼。Guido 的觀察是：**反正人類讀程式碼時就是看縮排判斷邏輯，那為什麼還要再寫一次大括號？讓縮排本身就是語法，就強迫所有人寫出整齊的程式碼**。三十多年後，Python 變成全世界用戶最多的語言之一，這個設計被證明是對的——你絕對不會看到一個 Python 專案因為「縮排風格不一致」吵架，因為根本不能不一致。

## 把這些湊在一起

本課從 Chapter 5 開始的範例會大量用到上面這些。先看個小例子，把這章學的東西全部用一次：

```python
def find_cheap_models(pricing, threshold):
    cheap = []
    for name, price in pricing.items():
        if price < threshold:
            cheap.append(name)
    return cheap

pricing = {
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "whisper-1": 0.006,
}

result = find_cheap_models(pricing, 1.0)
print(f"便宜的模型：{result}")
```

讀讀看你能不能跟著流程跑：函式定義、空 list、for 迴圈、if 條件、append、return、f-string——全部都在裡面。如果這段你大致看得懂，這章就過了。

## 小結

這章我們碰過：

1. 變數與字串（含 f-string）
2. `list`：有順序的容器
3. `dict`：用名字查資料的容器
4. `if / elif / else`：條件判斷
5. `for`：迴圈
6. `def`：定義函式
7. 縮排：Python 用空白標示邏輯區塊

下一章我們會碰檔案讀寫跟錯誤處理——這兩個你跑任何「真的有用」的程式都會用到。

## 練習

1. 建立一個 list 存五個你常用的網站名稱，用 for 迴圈把它們印出來。
2. 建立一個 dict，key 是水果名、value 是價格，找出價格大於 50 的水果。
3. 寫一個函式 `count_chinese(text)`，計算一段字串裡有多少個中文字（提示：用 for 對 `text` 做迴圈，每個字元如果在範圍 `'一' <= c <= '鿿'` 內就算一個）。
4. 故意把一行縮排寫錯，看看 Python 跳什麼錯誤訊息。把錯誤訊息看懂，是學程式的重要技能。
