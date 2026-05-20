# Chapter 13. Structured Output

到目前為止，模型回給我們的都是「人類看得懂的文字」。但實務上很多時候我們希望模型回的是「**程式能直接讀的資料**」——例如把一份會議紀錄拆成「標題、摘要、行動項」三個欄位，後續可以塞進資料庫或寄成 email。

這章我們學怎麼讓模型可靠地輸出 JSON。

## 為什麼不只是「請輸出 JSON」

最直觀的做法是用 prompt 喊話：

```python
response = client.responses.create(
    model="gpt-4o",
    instructions="請以下面 JSON 格式回應：{\"title\": \"...\", \"summary\": \"...\"}",
    input=meeting_text,
)
data = json.loads(response.output_text)
```

**這在 95% 的情況會成功**。但剩下 5%，你會踩到下面這些坑：

1. 模型在 JSON 前面加「以下是分析結果：」
2. 模型在 JSON 用單引號而不是雙引號
3. 模型多了一個 trailing comma
4. 模型把 JSON 包在 markdown 程式碼塊 ```` ```json ... ``` ```` 裡
5. 模型直接返回類似但不完全的格式

對寫 prototype 來說 5% 失敗率還可接受。但對「跑在生產的工具」來說，95% 不夠——你得寫一堆 try/except、清洗邏輯，最後還是會在最重要的場合炸給你看。

> **Tip** — Prompt-only 的 JSON 輸出在 2023-2024 年是常態的痛點。OpenAI 推出 JSON mode 跟後來的 Structured Outputs，就是為了根本解決這個問題——讓模型在生成階段就被「強制」遵守格式，不是「請它配合」。這跟把字串檢查改成型別檢查是同一類飛躍：從「希望對方做對」變成「規則上不可能做錯」。

## OpenAI 的解法：Structured Outputs

OpenAI 在 2024 年推出 Structured Outputs：**你定義一個 schema，OpenAI 保證模型輸出符合這個 schema**。

最簡單的用法：

```python
from pydantic import BaseModel
from openai import OpenAI

client = OpenAI()

class MeetingNote(BaseModel):
    title: str
    summary: str
    action_items: list[str]

response = client.responses.parse(
    model="gpt-4o",
    instructions="把下面這份會議紀錄整理成結構化資料。",
    input=meeting_text,
    response_format=MeetingNote,
)

note = response.output_parsed
print(note.title)
print(note.summary)
for item in note.action_items:
    print(f"- {item}")
```

幾個重點：

- **`pydantic.BaseModel`** 是定義 schema 的方式（pydantic 是 OpenAI SDK 的相依套件，自動會裝）
- **`client.responses.parse(...)`**（不是 `create`）會自動解析回傳成 Pydantic 物件
- **`response_format=MeetingNote`** 告訴模型「要符合這個型別」
- **`response.output_parsed`** 直接拿到型別化的 Python 物件

**不需要 `json.loads()`**、**不需要清洗**、**不需要 try/except 處理格式**——格式由 OpenAI 端強制保證。

## 一個完整範例：會議紀錄結構化

```python
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

class ActionItem(BaseModel):
    owner: str
    task: str
    due_date: str  # 用字串，因為 ISO date

class MeetingNote(BaseModel):
    title: str
    date: str
    attendees: list[str]
    summary: str
    key_decisions: list[str]
    action_items: list[ActionItem]

INSTRUCTIONS = """
你會收到一份會議逐字稿。請整理成結構化的會議紀錄。

規則：
1. 標題要簡短、能反映會議主題
2. 摘要 100 字內，講清楚會議目的與結論
3. Key decisions 列出明確的決議（不是討論的事項）
4. Action items 每一條要有負責人、任務、期限
5. 不要編造資訊；如果某個欄位逐字稿沒提到，留空字串或空 list
""".strip()

def structure_meeting(transcript: str) -> MeetingNote:
    response = client.responses.parse(
        model="gpt-4o",
        instructions=INSTRUCTIONS,
        input=transcript,
        response_format=MeetingNote,
    )
    return response.output_parsed
```

呼叫：

```python
note = structure_meeting(transcript)
print(f"主題：{note.title}")
print(f"日期：{note.date}")
print(f"摘要：{note.summary}")
print(f"\n決議：")
for d in note.key_decisions:
    print(f"  - {d}")
print(f"\n行動項：")
for item in note.action_items:
    print(f"  - {item.owner}：{item.task}（{item.due_date}）")
```

這個 `note` 物件可以直接：

- 存進資料庫
- 轉成 JSON 寫進檔案：`note.model_dump_json(indent=2)`
- 轉成 Python dict：`note.model_dump()`
- 跟其他系統交換

## Schema 設計的原則

實務上設計 schema 有幾個原則會讓品質好很多：

**1. 欄位名要對模型友善**——用英文 snake_case 比中文好（模型訓練時看到的英文 schema 例子多）。但欄位的「描述」可以用中文。

**2. 巢狀不要太深**——超過三層巢狀模型品質會掉。如果你有 5 層巢狀，可能該重新設計 schema。

**3. 給 description**——pydantic 支援 Field 加描述：

```python
from pydantic import BaseModel, Field

class MeetingNote(BaseModel):
    title: str = Field(description="會議主題，10 字內")
    summary: str = Field(description="摘要，100 字內")
    action_items: list[ActionItem] = Field(description="行動項清單")
```

description 會被傳給模型，幫它理解每個欄位該放什麼。

**4. 用 Enum 限制選項**——如果某個欄位只能是固定幾個值：

```python
from enum import Enum

class Priority(str, Enum):
    high = "高"
    medium = "中"
    low = "低"

class ActionItem(BaseModel):
    task: str
    priority: Priority
```

這樣模型不會回「緊急」「重要」這種模型自己發明的值，只會在 `高/中/低` 三選一。

> **Note** — 用 Enum 限制選項對「之後要寫 if 判斷」「之後要做統計」的場景超級重要。如果你不限制，模型今天回「高」、明天回「重要」、後天回「High」，你的程式只能 if 一堆 case，最後還是會漏。**Enum 一勞永逸**。

## 處理「資料不存在」的欄位

有時候輸入沒提到某個欄位，硬要模型編一個會出問題。比較好的做法：

**1. 用 Optional**——允許欄位是 `None`：

```python
from typing import Optional

class ActionItem(BaseModel):
    owner: str
    task: str
    due_date: Optional[str] = None  # 沒寫期限就是 None
```

**2. 用 list 不用 Optional list**——空 list 比 None 好處理：

```python
class MeetingNote(BaseModel):
    action_items: list[ActionItem]  # 沒有行動項時是 []，不是 None
```

**3. 在 instructions 明確說**：

> 規則：如果某個欄位逐字稿沒提到，留空字串或空 list，**不要編造**。

## 不只是 JSON：實務上的用途

Structured Outputs 不只用在會議紀錄。常見場景：

**1. 客戶回饋分類**

```python
class Feedback(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    category: Literal["bug", "feature", "praise", "question"]
    severity: Literal["low", "medium", "high"]
    summary: str
```

**2. 履歷解析**

```python
class Experience(BaseModel):
    company: str
    title: str
    start_year: int
    end_year: int | None
    description: str

class Resume(BaseModel):
    name: str
    email: str
    experiences: list[Experience]
```

**3. 從文章抽出實體**

```python
class Entity(BaseModel):
    name: str
    type: Literal["person", "company", "location", "date"]
    context: str

class Extraction(BaseModel):
    entities: list[Entity]
```

幾乎所有「把模糊文字變成結構化資料」的需求，都可以用 Structured Outputs 做。

## 限制與成本

- **不是所有模型支援**——`gpt-4o`、`gpt-4o-mini`、`o1` 支援；舊版 `gpt-3.5-turbo` 不支援
- **第一次呼叫某個 schema 會多花 0.5-1 秒**——OpenAI 後端要先「編譯」schema，但同 schema 後續呼叫不會多花時間
- **複雜 schema 會增加 token 用量**——schema 本身會被當輸入算 token

> **Warning** — Structured Outputs <strong>不會驗證內容</strong>。它保證「格式對」，但不保證「內容正確」。模型仍可能回給你一個 schema 完全正確、但內容是錯的（編造的）行動項。<strong>結構驗證跟事實驗證是兩回事</strong>——後者要靠 prompt 規則跟人類審核。

## 小結

1. **`response_format=YourModel`** 強制模型輸出符合 schema 的 JSON
2. **用 Pydantic 定義 schema**，欄位描述用 `Field(description=...)`
3. **Enum 限制選項**，避免模型發明新值
4. **不要編造**——明確指示「沒提到就留空」
5. **用 `client.responses.parse(...)`** 而不是 `create()`，並用 `output_parsed` 拿型別化結果
6. **保證格式對，不保證內容對**——事實正確性仍需人工核對

下一章我們學 streaming——讓使用者邊看模型生成、不要等到全部跑完。

## 練習

1. 設計一個 schema：把客戶評論分成「情緒、問題類型、嚴重度、摘要」四個欄位，用 Structured Outputs 抽出。
2. 修改本章的 `MeetingNote` schema，加上「會議時長（分鐘）」與「下次會議日期」兩個欄位。
3. 故意給模型一份不是會議紀錄的文字（例如新聞文章），看看它怎麼處理空欄位。
4. 用 `note.model_dump_json(indent=2)` 把結果寫進檔案，比較看看 JSON 結構。
