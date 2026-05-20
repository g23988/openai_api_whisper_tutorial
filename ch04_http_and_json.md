# Chapter 4. HTTP 與 JSON 基礎

上一章我們講過，API call 就是「程式之間的一通電話」。這章我們把這通電話拆開看：訊息是怎麼包裝的、傳哪邊去的、收到的回應裡有什麼。

理解這層你會獲得兩個東西：

1. 看到陌生 API 文件不會慌（包括 OpenAI 文件）
2. 出錯的時候看得懂錯誤訊息（401、429、500 各是什麼意思）

我們會盡量不下沉到太底層的細節——那是後端工程師的工作。我們只挖到「會用、能除錯」的深度。

## HTTP 是什麼

HTTP（HyperText Transfer Protocol）是 1991 年由 Tim Berners-Lee 發明的協議，原本只是為了讓網頁瀏覽器可以從伺服器抓網頁。三十多年後，HTTP 變成了**幾乎所有網路服務之間溝通的標準語言**——不只網頁，連 OpenAI API、Stripe 付款、Google Maps、你家路由器的設定頁，背後都是 HTTP。

> **Tip** — HTTP 變成「萬用通訊協定」是有歷史偶然性的。1990 年代有很多其他協定（FTP、Gopher、WAIS），但 HTTP 因為跟著瀏覽器一起爆紅，加上設計足夠簡單彈性，後來其他協定要做的事都被 HTTP 吃下來。今天的「HTTP API」其實是 HTTP 的「副業」——但這個副業比正業還大。

一個 HTTP 請求（request）有四個部分：

1. **Method**：動詞，常見的有 `GET`（要資料）、`POST`（送資料）、`PUT`、`DELETE`
2. **URL**：要送到哪裡，例如 `https://api.openai.com/v1/responses`
3. **Headers**：附加資訊，例如「我是誰」「我送什麼格式的資料」
4. **Body**：資料本體，通常是 JSON

回應（response）有三個部分：

1. **Status code**：三位數，告訴你成功還失敗
2. **Headers**：類似 request，但是反向
3. **Body**：回傳的資料，也通常是 JSON

OpenAI 呼叫 API 的時候，背後就是這樣的一封信。

## 一個真實的 OpenAI API 請求長這樣

如果你不用 SDK、用最原始的 HTTP 工具（例如 `curl`）呼叫 OpenAI，會像這樣：

```bash
curl https://api.openai.com/v1/responses \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "input": "用一句話解釋什麼是 API。"
  }'
```

把這封信拆開：

- **URL**：`https://api.openai.com/v1/responses` 是 OpenAI 的 Responses API 入口
- **Method**：`-d` 自動讓 curl 用 `POST`（因為有資料要送）
- **Headers**：
  - `Authorization: Bearer YOUR_API_KEY` 告訴 OpenAI「我是誰」
  - `Content-Type: application/json` 告訴 OpenAI「我送的資料是 JSON」
- **Body**：那串 `{"model": "gpt-4o", ...}` 就是 JSON

OpenAI 收到後會回你一封信，body 也是一個 JSON，內容類似：

```json
{
  "id": "resp_abc123",
  "model": "gpt-4o",
  "output": [
    {
      "type": "message",
      "content": [
        {
          "type": "output_text",
          "text": "API 是讓不同程式溝通的標準化介面。"
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 12,
    "output_tokens": 15
  }
}
```

OpenAI Python SDK 在做的事，**就是把你呼叫的 `client.responses.create(...)` 翻譯成上面那封信、送出去、然後把回傳的 JSON 拆開包成 Python 物件給你**。沒有魔法，全部都是 HTTP。

> **Note** — 「Bearer Token」是 HTTP 的身份驗證方式之一，意思是「持有這張票的人就有權限」。所以你的 API key 就是那張票——誰拿到都能用。這也是為什麼保護 key 這麼重要。

## JSON 是什麼

JSON（JavaScript Object Notation）是一種「結構化資料的文字格式」。它長得跟 Python 的 `dict` 跟 `list` 非常像：

```json
{
  "name": "OpenAI",
  "founded": 2015,
  "models": ["gpt-4o", "gpt-4o-mini", "whisper-1"],
  "active": true
}
```

JSON 支援的資料型別只有六種：

| JSON 型別 | 範例 | 對應的 Python |
|---|---|---|
| string | `"hello"` | `str` |
| number | `42`、`3.14` | `int` / `float` |
| boolean | `true` / `false` | `True` / `False` |
| null | `null` | `None` |
| array | `[1, 2, 3]` | `list` |
| object | `{"a": 1}` | `dict` |

就這六種。沒有 datetime、沒有 set、沒有函式——故意設計得很小，因為**要每個程式語言都能解讀，得用最低公分母**。日期通常用字串表示（例如 `"2025-01-15T10:30:00Z"`），由程式自己解析。

> **Tip** — JSON 是 2001 年由 Douglas Crockford 推廣的格式。在那之前，網路上的標準是 XML（看起來像 HTML 那種）。XML 很強大，但也很囉嗦——同一份資料，XML 通常比 JSON 多兩倍以上的字。JSON 的設計哲學是「**剛剛好就好**」，結果完勝。十年內 XML 在 web API 領域基本被淘汰，今天幾乎所有現代 API 都用 JSON，包括 OpenAI、Stripe、GitHub、Twitter（X）。

## JSON 的常見坑

JSON 看起來簡單，但有幾個地雷新手必踩：

**1. 不能有逗號在最後一個元素後面**

```json
{
  "a": 1,
  "b": 2,
}
```

最後一個 `2,` 那個逗號在 Python `dict` 可以、在 JavaScript 物件可以，**但 JSON 不行**。這叫「trailing comma」，標準 JSON 會直接 parse 失敗。

**2. 字串只能用雙引號**

```json
{ 'name': 'OpenAI' }
```

JSON 不允許單引號，必須用雙引號。

**3. 不能寫註解**

JSON 標準不支援註解（雖然有些 parser 會接受 `//...`，但別依賴）。要加說明只能用一個 key 假裝是註解，例如 `"_comment": "這欄之後要刪掉"`。

> **Warning** — Python 的 dict 跟 JSON 看起來很像，但有幾個差異會害你：(1) Python 用 <code>True / False / None</code>，JSON 用小寫的 <code>true / false / null</code>；(2) Python 允許單引號跟尾巴逗號，JSON 不允許。在 Python 裡寫 dict 隨意，但**輸出成 JSON 給別人時要小心**。用 <code>json.dumps()</code> 而不是手動拼字串。

## Python 裡怎麼操作 JSON

Python 內建 `json` 模組，兩個最常用的函式：

```python
import json

# Python 物件 → JSON 字串
data = {"model": "gpt-4o", "input": "Hello"}
json_str = json.dumps(data)
print(json_str)
# {"model": "gpt-4o", "input": "Hello"}

# JSON 字串 → Python 物件
parsed = json.loads(json_str)
print(parsed["model"])
# gpt-4o
```

`dumps` 是 "dump string"（轉出去成字串），`loads` 是 "load string"（從字串讀進來）。讀寫檔案用 `dump` 跟 `load`（不加 s）：

```python
with open("config.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
```

`ensure_ascii=False` 讓中文以原樣輸出而不是 `中文`，`indent=2` 讓檔案有縮排，人類看得懂。

## HTTP Status Code：三位數的故事

當 OpenAI 回應你，status code 會告訴你成敗。三位數的開頭代表大類：

- **2xx：成功**。你要的東西在 body 裡，盡情用
- **3xx：重新導向**。「你要的東西搬家了，去這個新網址」
- **4xx：你的請求有問題**。少帶 key、格式錯、權限不夠
- **5xx：對方伺服器壞了**。不是你的問題，重試或等等

對 OpenAI API 來說，你會踩到的主要是 4xx：

| Code | 名稱 | 通常意思 |
|---|---|---|
| 200 | OK | 成功 |
| 400 | Bad Request | 你送的 JSON 格式錯誤，或缺必要欄位 |
| 401 | Unauthorized | API key 錯了、過期了、或沒帶 |
| 403 | Forbidden | API key 對，但這個帳號沒這個模型的權限 |
| 404 | Not Found | URL 打錯，或模型名稱不存在 |
| 429 | Too Many Requests | 打太快，超過 rate limit |
| 500 | Internal Server Error | OpenAI 那邊出問題，重試或等 |
| 503 | Service Unavailable | OpenAI 系統忙不過來，等等再試 |

> **Note** — HTTP status code 是 1991 年 Tim Berners-Lee 跟同事一起設計的，其中 404 因為太常見已經變成流行文化的一部分（很多網站把 404 頁面做得很有梗）。418 是個彩蛋——"I'm a teapot"，1998 年愚人節玩笑寫進 RFC 的，意思是「我是茶壺，不能煮咖啡」。HTTP 標準是有幽默感的。

## 從這裡看 SDK 在幹嘛

回頭看 Python SDK：

```python
response = client.responses.create(
    model="gpt-4o",
    input="用一句話解釋什麼是 API。",
)
```

當你呼叫這行，SDK 在幫你做的事：

1. 把 `model` 跟 `input` 包成 JSON
2. 加上 `Authorization: Bearer ...`（從環境變數讀 API key）
3. 加上 `Content-Type: application/json`
4. 用 `POST` method 送到 `https://api.openai.com/v1/responses`
5. 收到回應，看 status code
6. 如果是 4xx 或 5xx，丟出對應的 Python exception（例如 `AuthenticationError`、`RateLimitError`）
7. 如果是 200，把回傳的 JSON 解析成 Python 物件

**SDK 不是魔法，是幫你省下這些重複動作的工具**。理解這層，你之後看 OpenAI 文件（或任何 REST API 文件）都會很快上手——因為所有 REST API 都是這個模式。

## 小結

這章把 API call 的「內部」拆開來看：

1. **HTTP 是萬用網路通訊協定**——request 有 method、URL、headers、body；response 有 status code、headers、body
2. **JSON 是現代 API 的標準資料格式**——簡單、跨語言、剛剛好
3. **Python `json` 模組**：`dumps/loads` 轉字串，`dump/load` 操作檔案
4. **HTTP status code 看開頭分類**：2xx 成功、4xx 你的問題、5xx 對方問題
5. **OpenAI SDK 就是 HTTP+JSON 的包裝**——理解這層，所有 REST API 都通

下一章開始我們要動手——把 Python 環境真正設定起來，準備在 Chapter 6 打第一通 API call。

## 練習

1. 把這個 Python dict 用 `json.dumps()` 轉成 JSON 字串，並用 `indent=2` 讓它有排版：`{"name": "OpenAI", "models": ["gpt-4o", "o1"], "founded": 2015}`
2. 故意寫一個有 trailing comma 的 JSON 字串，丟給 `json.loads()`，看看跳什麼錯。
3. 解釋為什麼 401 和 403 是不一樣的錯——一個是「沒帶有效身份」，另一個是「身份是真的但沒權限」。生活中可以舉一個類似的例子嗎？
4. 看 OpenAI 文件的 API reference 頁，找一個你沒呼叫過的 endpoint（例如 `images.generate`），看它的 request body 範例長什麼樣。能不能光看 JSON 結構就猜出它在做什麼？
