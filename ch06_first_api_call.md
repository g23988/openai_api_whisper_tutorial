# Chapter 6. 第一個 Responses API 程式

前面五章把路鋪好了：終端機會用了，Python 環境裝起來了，API key 也設好了。這章我們終於要打第一通電話給 OpenAI——而且程式短到你可能會懷疑這樣就夠了嗎。

確實就這樣。整段程式大概十行，但這十行是之後每一個 API call 的骨架。看懂這一段，後面所有範例都是它的延伸而已。

## 最小可運作的程式

打開你的編輯器，建立一個叫 `hello.py` 的檔案，貼進下面這段：

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-4o",
    input="用一句話解釋什麼是 API。",
)

print(response.output_text)
```

存檔，回到終端機，確認你還在啟動 `.venv` 的狀態，然後執行：

```bash
python hello.py
```

如果一切順利，你會看到模型回給你的一句話。每次跑出來的句子都可能不太一樣，這是正常的。

> **Note** — 如果你看到 `ModuleNotFoundError: No module named 'openai'`，代表你不在虛擬環境裡，或者套件沒裝。回 Chapter 5 確認 `source .venv/bin/activate` 跟 `pip install openai` 都做過了。

## 一行一行讀懂它

短歸短，這段程式做了四件事。我們慢慢看。

```python
from openai import OpenAI
```

第一行把 `OpenAI` 這個類別從 `openai` 套件匯入進來。這個套件就是我們在 Chapter 5 用 `pip install openai` 裝的那一個，正式名稱叫做「OpenAI Python SDK」。

SDK 是 Software Development Kit 的縮寫，講白話就是「人家寫好的工具包」。沒有它，我們得自己組 HTTP request、處理 JSON、處理錯誤回應；有它，我們只要呼叫幾個 Python 函式就好。Chapter 4 講過 SDK 背後其實就是在送 HTTP，這裡是第一次親手用到。

```python
client = OpenAI()
```

第二件事是建立一個「客戶端」物件。你可以把 `client` 想成一支已經設定好的電話：之後所有要打給 OpenAI 的呼叫，都從這支電話打出去。

這一行為什麼不需要寫 API key？因為 `OpenAI()` 在建立時會自動去找環境變數 `OPENAI_API_KEY`。我們在 Chapter 5 已經設好了，所以這裡可以省略。

> **Warning** — 千萬不要為了方便寫成 `OpenAI(api_key="sk-...")`，把 key 硬編在程式碼裡。一旦你把程式碼推到 GitHub，這個 key 就等於公開了。OpenAI 的偵測機器人會立刻發信通知你 key 已被撤銷，這還算好的下場——更糟的是被人撿去打到你帳號額度爆掉。

```python
response = client.responses.create(
    model="gpt-4o",
    input="用一句話解釋什麼是 API。",
)
```

這裡是真正的重點。`client.responses.create(...)` 就是「我要呼叫 Responses API」的意思。Responses API 是 OpenAI 目前推薦給文字生成任務的主要介面，本課所有文字相關的呼叫都會用它。

`model` 告訴 OpenAI「我要用哪個模型」。我們選了 `gpt-4o`，這是個適合大部分一般任務、品質穩定、價格中等的選擇。

`input` 就是你想問模型的話。可以是一句話、一段文章、甚至一份完整文件，只要不超過模型的長度限制都行。

> **Tip** — `model` 跟 `input` 是這個 API 最常用的兩個參數，剩下的（`instructions`、`temperature`、`stream`...）都是進階用法，我們會在後面幾章慢慢介紹。剛開始不用想太多。

```python
print(response.output_text)
```

最後一行把回應印出來。注意我們印的是 `response.output_text`，不是 `response` 本身。

`response` 是一個 Python 物件，裡面包了一大堆資訊：用了多少 token、用了哪個模型版本、輸出有沒有被內容過濾、產生時間、各種 metadata。但 99% 的時候你只在意「模型講了什麼」，所以 SDK 貼心地提供了 `output_text` 這個快捷屬性，把純文字直接撈出來。

如果你好奇 `response` 裡面長什麼樣，可以加一行：

```python
print(response)
```

跑跑看，會發現是一坨結構化的資料。等到 Chapter 9 處理 Speech to Text、Chapter 13 處理 Structured Output 時，我們會回頭挖這個物件的更多欄位。

## 背後發生了什麼

你按下 Enter 那一刻，下面這串事情大概在一兩秒內全部發生了：

1. SDK 把你的 `input` 跟 `model` 包成一份 JSON
2. SDK 用你的 API key 當 header，把這份 JSON 透過 HTTPS 送到 `api.openai.com`
3. OpenAI 的伺服器收到、跑模型、產生回應
4. 伺服器把結果包成 JSON 回傳
5. SDK 解析 JSON，包成 Python 物件交給你

整個過程是 Chapter 4 講的 HTTP request/response 的具體實現。SDK 把這些細節都藏起來了，但你心裡要有「這就是在送 HTTP」的概念——除錯的時候會很有用。

## 常見出錯狀況

第一次跑通常會卡幾種地方，每個都很典型：

**`AuthenticationError: Incorrect API key`**——多半是 API key 沒設好，或者設了但這個終端機 session 沒讀到。確認你在當前終端機跑 `echo $OPENAI_API_KEY`（macOS / Linux）或 `echo %OPENAI_API_KEY%`（Windows）有東西出來。

**`RateLimitError: 429`**——你呼叫太快、或者你的 OpenAI 帳號還沒有付款方式、或者額度用完了。打開 OpenAI dashboard 看一下帳號狀態。

**`NotFoundError: The model 'xxx' does not exist`**——模型名稱打錯，或者你的帳號沒這個模型的權限。確認你打的是 `gpt-4o` 而不是 `gpt4o` 或 `GPT-4o`。

**程式跑完沒輸出、也沒錯誤訊息**——很可能是你忘了 `print(...)`。我看過不少學員。

> **Note** — 看到陌生的錯誤訊息，先把整段錯誤複製貼到 Google 或 ChatGPT 問。OpenAI 的錯誤訊息其實寫得算清楚，多半英文讀懂大半就知道問題在哪。

## 小結

這章我們做了四件事：匯入 SDK、建立 client、呼叫 Responses API、印出結果。短短十行，卻是這整套課程的核心模式——之後不管做摘要、改寫、會議紀錄、語音轉文字，都是這個骨架加上不同參數而已。

接下來的 Chapter 7，我們會開始認真寫 prompt，讓模型的回答從「能用」變成「真的好用」。

## 練習

1. 把 `input` 改成「用三個條列說明 OpenAI API 可以做什麼」，觀察模型輸出怎麼變化。
2. 加上一個迴圈，連續呼叫五次同一個 prompt，看看每次的回答有沒有不一樣。
3. 改成從命令列讀取問題：執行 `python hello.py "你的問題"`，讓程式把第一個參數當成 `input`（提示：用 `sys.argv`）。
4. 跑一次後，把 `print(response)` 加進去，看看完整的回應物件長什麼樣，找出裡面 `usage` 欄位是什麼。
