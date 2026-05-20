# Chapter 16. 安全、成本與錯誤排除

到目前為止我們做的工具都能跑。但「能跑」跟「敢給人用」是兩回事。這章我們處理三個會讓你晚上睡不好的問題：

1. **API key 怎麼不被偷**（被偷會花你的錢）
2. **API 成本怎麼估、怎麼控制**（避免月底收到嚇人的帳單）
3. **錯誤怎麼處理**（讓使用者看到「請重試」而不是「TypeError: 'NoneType'...」）

這章的內容看起來不性感，但**它決定了你的工具能不能真的拿出去用**。

## 第一部分：API Key 安全

OpenAI API key 是字串、沒有「設備綁定」、誰拿到都能用。所以保護它**完全靠你**。

### 三條鐵律

**1. 永遠不要把 key 寫進程式碼**

```python
# 絕對不要這樣
client = OpenAI(api_key="sk-proj-xxxxx")
```

正確做法：用環境變數（Chapter 5 教過）：

```python
load_dotenv()
client = OpenAI()  # 自動讀 OPENAI_API_KEY
```

**2. 永遠不要把 key 放進前端**

```html
<!-- 絕對不要這樣 -->
<script>
  const apiKey = "sk-proj-xxxxx";
  fetch("https://api.openai.com/v1/...", { headers: { Authorization: `Bearer ${apiKey}` } });
</script>
```

瀏覽器的 JavaScript 任何人都能用 F12 看到。如果你做的是「網頁讓使用者呼叫 OpenAI」，**一定要透過你的後端轉手**——前端打你的 server，server 用你的 key 打 OpenAI。

**3. 永遠不要把 key 提交到 git**

`.env` 進 `.gitignore`（Chapter 15 講過）。**特別小心截圖**——很多人寫教學影片時不小心把 key 截進去，傳到 YouTube 就洩漏了。

> **Warning** — GitHub 有自動掃描，偵測到 commit 含 OpenAI key 會立刻撤銷它。但 <strong>bot 不總是夠快</strong>——已經有真實案例是 key 在被撤銷前的幾分鐘內被人撿去打了幾百美金。除了等 GitHub 撤銷，你應該主動到 OpenAI dashboard 撤銷那把 key。

### 多人專案怎麼共用

如果你有同事或朋友要一起開發，**不要把 key 寄給他們**。讓每個人到 OpenAI dashboard 建立**自己的 key**。OpenAI 允許一個帳號開多把 key，並且各自可以設用量上限。

對團隊：用 OpenAI 的 **Project** 功能——每個專案可以單獨設預算、權限、用量監控。

### 如果懷疑 key 洩漏

立刻：

1. 到 OpenAI dashboard → API keys
2. 找到那把 key，點 Revoke
3. 建立新的 key
4. 更新 `.env`
5. 檢查 git 歷史，確認 key 不在裡面：`git log -p | grep -i "sk-"`

> **Tip** — 養成<strong>每 3-6 個月輪換 key</strong> 的習慣，即使沒有懷疑洩漏。這是企業安全的標準做法——「key 像衣服，不是越用越久越好」。OpenAI 允許你同時保留多把 key，輪換時可以無痛切換。

## 第二部分：成本控制

OpenAI API 按 token 計費。**搞不清楚 token 是什麼，帳單就會搞不清楚**。

### Token 是什麼

Token 是模型處理文字的「基本單位」，**不完全等於字**。粗略對應：

- **1 token ≈ 0.75 個英文單字 ≈ 0.5 到 1 個中文字**
- 句點、逗號、空格也算 token

舉例：

| 文字 | 大約 tokens |
|---|---|
| `hello` | 1 |
| `hello world` | 2 |
| `你好` | 2-3 |
| `今天天氣很好` | 5-6 |
| 一段 100 字中文 | 100-200 |
| 一份 5000 字會議紀錄 | 5000-10000 |

要精確算，用 OpenAI 出的 `tiktoken` library：

```bash
pip install tiktoken
```

```python
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-4o")
text = "請用一句話解釋什麼是 API。"
tokens = encoding.encode(text)
print(f"Token 數：{len(tokens)}")
print(f"字元數：{len(text)}")
```

跑跑看，你會發現中文 1 個字常常等於 2-3 個 token——比英文貴。

### 成本估算

OpenAI 公布的定價以「每百萬 token」為單位。本書寫作時的範例價格（請以 OpenAI 官方為準）：

| 模型 | Input | Output |
|---|---|---|
| `gpt-4o` | $2.50 / 1M | $10 / 1M |
| `gpt-4o-mini` | $0.15 / 1M | $0.60 / 1M |
| `whisper-1` | $0.006 / 分鐘 | - |
| `gpt-4o-transcribe` | $0.006 / 分鐘 | - |

實用估算範例：

**情境 1：1 小時會議轉錄 + 摘要**

- 轉錄：60 分鐘 × $0.006/分鐘 = $0.36
- 假設逐字稿 8000 字（≈ 12000 tokens 中文）
- 摘要：input 12k + output 500 ≈ $0.03（用 gpt-4o）
- **總計：約 $0.39**

**情境 2：每天處理 100 個客戶回饋分類**

- 每篇 500 字（≈ 750 tokens input） + 50 tokens output
- 用 gpt-4o-mini：100 × (750×0.15 + 50×0.6) / 1M = $0.014/天
- **一個月：約 $0.42**

**情境 3：給 1000 個使用者各跑 10 次摘要**

- 萬一你用 gpt-4o：10000 × (3000 input + 500 output) ≈ $125
- 改用 gpt-4o-mini：≈ $7.50
- **選錯模型差 17 倍**

> **Note** — 一個務實的省錢原則：<strong>能用 gpt-4o-mini 就用 mini</strong>。對「分類、抽取、結構化、簡單摘要」這類任務，mini 的品質完全夠用，價格只有 gpt-4o 的 1/17。<strong>只在真的需要長文推理、複雜邏輯的場景才用 gpt-4o 或 o1</strong>。

### 估算函式

寫一個估算工具：

```python
import tiktoken

PRICING = {
    "gpt-4o":         {"input": 2.50,  "output": 10.0},
    "gpt-4o-mini":    {"input": 0.15,  "output": 0.60},
}

def estimate_cost(text: str, model: str, expected_output_tokens: int = 500) -> float:
    encoding = tiktoken.encoding_for_model(model)
    input_tokens = len(encoding.encode(text))
    p = PRICING[model]
    cost = (input_tokens * p["input"] + expected_output_tokens * p["output"]) / 1_000_000
    return cost

text = open("meeting.txt", encoding="utf-8").read()
print(f"gpt-4o:      ${estimate_cost(text, 'gpt-4o'):.4f}")
print(f"gpt-4o-mini: ${estimate_cost(text, 'gpt-4o-mini'):.4f}")
```

跑之前先估算——對「一次處理很多檔案」的批次任務尤其重要。

### 設定 OpenAI 帳號的硬上限

OpenAI dashboard 提供「**Monthly budget**」設定：

- 設定每月最高花費（例如 $50）
- 超過會自動停止 API 服務
- 你會收到 email 警告

**這是「就算程式有 bug 也不會花爆」的最後一道防線**。強烈建議所有人都設一個合理的上限。

> **Warning** — 沒設上限的話，一個寫錯的無限迴圈可能在幾小時內花掉幾百美金。曾經有真實案例：開發者寫了一個 retry 邏輯但忘記退避，網路一抽風就連續打 API 幾千次。<strong>Monthly budget 是免費的保險，務必設定</strong>。

## 第三部分：錯誤處理

實際使用 API 會遇到各種錯誤。**好的錯誤處理 = 使用者看到「請檢查網路」而不是 Python traceback**。

### 常見 OpenAI 錯誤

```python
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    RateLimitError,
)

try:
    response = client.responses.create(...)
except AuthenticationError:
    print("API key 無效，請檢查 .env")
except RateLimitError:
    print("超過呼叫頻率上限，請稍候再試")
except APIConnectionError:
    print("無法連線 OpenAI，請檢查網路")
except BadRequestError as e:
    print(f"請求格式錯誤：{e}")
except APIError as e:
    print(f"OpenAI 伺服器錯誤：{e}")
```

對使用者導向的工具，**把這些 exception 包裝成清楚的訊息**。對技術人員的工具，也許可以印出更多細節幫除錯。

### 重試與指數退避

網路問題、暫時的 rate limit 通常等一下就好。標準做法是「指數退避重試」（Chapter 11 教過）：

```python
import time

def call_with_retry(fn, max_attempts: int = 3):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except (RateLimitError, APIConnectionError) as e:
            if attempt == max_attempts:
                raise
            wait = 2 ** attempt   # 2, 4, 8 秒
            print(f"重試 {attempt}/{max_attempts}（{wait}s）：{e}")
            time.sleep(wait)
```

OpenAI Python SDK 1.0+ 內建重試，但只對特定錯誤生效，自己包一層比較有彈性。

### Timeout 設定

預設的 API timeout 很長（120 秒）。對「使用者在 GUI 按按鈕」的情境，10 秒沒回應就該 fallback：

```python
client = OpenAI(timeout=30.0)
```

或單次呼叫：

```python
response = client.responses.create(
    model="gpt-4o",
    input="...",
    timeout=10.0,
)
```

> **Note** — 對長任務（streaming、大量 token），timeout 要設長一點。對短任務（分類、簡單問答），timeout 設短可以早點 fallback。<strong>沒有一個 timeout 值對所有情境都對</strong>，依任務調整。

### 印出有用的錯誤訊息

對使用者：

```python
print("錯誤：無法連線 OpenAI。請檢查網路後重試。", file=sys.stderr)
```

對開發者（你自己除錯）：

```python
import traceback

try:
    ...
except Exception as e:
    print(f"未預期錯誤：{type(e).__name__}: {e}", file=sys.stderr)
    traceback.print_exc()
```

**不要把 raw exception 丟給終端使用者看**。把它記到 log file，給使用者看精簡版。

## 三方面整合

把這章的東西組合成一個「**生產可用**」的 API 呼叫包裝：

```python
import logging
import time
from openai import OpenAI, RateLimitError, APIConnectionError, AuthenticationError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

client = OpenAI(timeout=30.0)

def safe_call(fn, max_retries: int = 3) -> str:
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except AuthenticationError:
            raise RuntimeError("API key 無效，請檢查 .env 設定")
        except RateLimitError as e:
            if attempt == max_retries:
                raise RuntimeError("API 呼叫太頻繁，請稍候再試") from e
            time.sleep(2 ** attempt)
            log.warning(f"Rate limit，{2**attempt}s 後重試")
        except APIConnectionError as e:
            if attempt == max_retries:
                raise RuntimeError("無法連線 OpenAI，請檢查網路") from e
            time.sleep(2 ** attempt)
            log.warning(f"連線失敗，{2**attempt}s 後重試")
    raise RuntimeError("超過最大重試次數")
```

使用：

```python
try:
    text = safe_call(lambda: client.responses.create(
        model="gpt-4o",
        input="hello",
    ).output_text)
    print(text)
except RuntimeError as e:
    print(f"錯誤：{e}", file=sys.stderr)
```

## 小結

**安全**：

1. Key 不進程式碼、不進前端、不進 git
2. 用 `.env` + `python-dotenv`
3. 懷疑洩漏立刻 revoke
4. 每 3-6 個月輪換 key

**成本**：

1. Token ≠ 字，中文比英文貴
2. `tiktoken` 算精確值
3. 能用 gpt-4o-mini 就用 mini（差 17 倍）
4. **OpenAI dashboard 設 Monthly budget**——免費保險
5. 大量任務先估算、再批次跑

**錯誤**：

1. catch 具體 exception，不要 catch-all
2. 用指數退避重試
3. 設 timeout
4. 給使用者精簡訊息，把細節記 log

下一章我們把這套課所有學過的東西串成期末專案——一個完整的會議逐字稿工具，可以給家人朋友用。

## 練習

1. 到 OpenAI dashboard，設定 Monthly budget（例如 $20）。如果你還沒設過，這是這章最重要的練習。
2. 用 `tiktoken` 算你手邊一份長文件的 token 數，估算用 gpt-4o 跟 gpt-4o-mini 各會花多少錢。
3. 把 Chapter 11 的長音檔轉錄工具加上 `safe_call`，跑一次故意斷網的場景，確認重試與錯誤訊息運作正常。
4. 在 `.gitignore` 跟 README 提醒部分檢查你的專案——確認沒有任何地方意外洩漏 key（截圖、commit 歷史、README 範例）。
