# Chapter 14. Streaming

當你用 ChatGPT，會發現它回答時是「邊想邊打字」——一個字一個字浮現，而不是等整段都生成完才一次顯示。這種「邊產生邊呈現」的體驗叫做 **streaming**。

不只 ChatGPT，OpenAI API 也支援 streaming。這章我們學怎麼用它，以及為什麼它對使用者體驗這麼重要。

## 為什麼 Streaming 重要

想像兩個情境：

**情境 A（無 streaming）**：使用者按下「產生摘要」按鈕。畫面什麼都沒動。10 秒過去，使用者開始懷疑是不是當機。15 秒，使用者想關掉視窗。20 秒，整段摘要突然全部跳出來。

**情境 B（有 streaming）**：使用者按下按鈕。一秒內，第一行文字開始出現。文字持續流動。20 秒後整段完成。

**兩個情境總共花的時間一樣**。但情境 A 讓使用者覺得「等了好久、不確定有沒有壞掉」，情境 B 讓使用者覺得「系統在工作、很快、很自然」。

這個感受差異有幾個心理學名詞：**感知速度（perceived speed）**、**等待焦慮（waiting anxiety）**。對任何超過 3 秒的操作，streaming 都會讓體驗好得多。

> **Tip** — ChatGPT 在 2022 年 11 月發布時，<strong>「打字機效應」是它最讓人印象深刻的設計之一</strong>。連 Sam Altman 都在訪談裡提過：streaming 介面讓使用者覺得 AI「在思考」，而不是「在計算」——前者親近，後者冰冷。技術上 streaming 並沒讓模型跑更快，但用戶體驗的差距是天差地遠。這也是為什麼後來所有 LLM 產品（Claude、Gemini、Copilot）都跟著做了 streaming UI。

## 技術原理：Server-Sent Events

Streaming 在 HTTP 層用的是 **Server-Sent Events (SSE)** 協定：

- 一般 HTTP request：client 送請求，server 一次回完，連線結束
- SSE：client 送請求，server 維持連線開著，**分批**送資料，最後才關閉

對 OpenAI API 來說：模型一邊產生 token，一邊就把已產生的部分送出去。client 收到一段就顯示一段。

> **Note** — SSE 是 HTML5 的標準，跟 WebSocket 不一樣——SSE 是單向的（server → client），WebSocket 是雙向的。SSE 簡單很多，剛好夠用在「server 推進度給 client」這個場景。OpenAI 在 streaming endpoint 一律用 SSE。

## 在 Python 用 Streaming

把 Chapter 6 的範例改成 streaming 版本：

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

stream = client.responses.create(
    model="gpt-4o",
    input="請用 300 字介紹 OpenAI API 的用途。",
    stream=True,
)

for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
print()  # 結束時加個換行
```

跑這段程式，你會看到文字在終端機**逐字顯示**——跟 ChatGPT 介面一樣。

幾個重點：

- **`stream=True`**：開啟 streaming 模式
- **回傳是個 generator**（迭代器），不是一次回完的物件
- **`event.type == "response.output_text.delta"`**：每來一段文字會觸發這個事件
- **`event.delta`**：這次新增的那一段文字
- **`flush=True`**：強制 Python 立刻把東西印出來，不要 buffer

`flush=True` 很關鍵——Python 預設會把 print 的內容 buffer 起來，等到一定量才寫到螢幕。對 streaming 來說這會破壞效果。

> **Warning** — 忘記 <code>flush=True</code> 是 streaming 新手最常踩的坑。表面上看起來「不會動，等很久突然全部跑出來」——還以為 streaming 沒生效，其實是被 buffer 卡住了。<strong>任何 streaming 的 print 都要加 <code>flush=True</code></strong>。

## 事件類型：不只是文字

Streaming 回的事件不只 `output_text.delta`。完整事件流長這樣：

```text
response.created           # 開始
response.output_item.added # 新增一個輸出項目
response.output_text.delta # 文字增量（最常用）
response.output_text.delta
response.output_text.delta
...
response.output_text.done  # 文字結束
response.completed         # 整個請求結束
```

對「只想顯示文字」的情境，只看 `.delta` 就好。對「想知道進度、總 token 數」的情境，看 `response.completed` 那個事件，它的 `event.response.usage` 有完整資訊。

完整處理：

```python
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
    elif event.type == "response.completed":
        print()  # 換行
        print(f"\n總共用 {event.response.usage.total_tokens} tokens")
```

## 在 Streamlit 用 Streaming

回到上一章我們的 GUI 工具。Streamlit 有個 `st.write_stream()` 方法，**完美對接 OpenAI 的 streaming**：

```python
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

prompt = st.text_area("問題", height=100)

if st.button("送出") and prompt:
    def generate():
        stream = client.responses.create(
            model="gpt-4o",
            input=prompt,
            stream=True,
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    st.write_stream(generate())
```

`st.write_stream()` 接受一個 generator，會把每次 `yield` 的文字即時顯示到畫面上。**這就跟 ChatGPT 介面完全一樣了**——幾行 Python 達成。

## 真實場景：摘要工具加上 Streaming

把 Chapter 8 的摘要工具改成 streaming 版：

```python
# summarize_stream.py
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

INSTRUCTIONS = "你是一位中文編輯，把文字整理成清楚的摘要。"

def summarize_stream(text: str) -> None:
    stream = client.responses.create(
        model="gpt-4o",
        instructions=INSTRUCTIONS,
        input=text,
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print()  # 結束換行

if __name__ == "__main__":
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    summarize_stream(text)
```

對長文摘要來說，這個版本體驗好太多——使用者看到模型「邊讀邊想邊寫」，不會有「按下去等到天荒地老」的感覺。

## Streaming 跟 Structured Output 能一起用嗎

可以，但稍微麻煩一點。`client.responses.parse(...)` 也支援 streaming：

```python
with client.responses.stream(
    model="gpt-4o",
    instructions="...",
    input=meeting_text,
    response_format=MeetingNote,
) as stream:
    for event in stream:
        if event.type == "content.delta":
            # 部分 JSON
            ...

final = stream.get_final_response()
note = final.output_parsed
```

對結構化輸出來說 streaming 比較少用——因為「半個 JSON」對 UI 沒意義。但有些進階場景（例如想顯示「正在生成標題...正在生成摘要...」這種分階段進度）會用到。

## Streaming 的取捨

**優點**：

- 使用者體感速度快很多
- 對長任務（300+ 字輸出）尤其有感
- 能在生成中途取消（按 Ctrl+C），省 token

**缺點**：

- 程式碼複雜度高一點
- 錯誤處理麻煩——可能中途失敗
- 不容易做「同時呼叫多個 API、整合結果」的場景

> **Note** — 一個務實的判斷：<strong>如果輸出短於 100 個字，不必用 streaming；超過 200 個字，streaming 強烈推薦</strong>。對「快速分類」「短摘要」這類任務，等 2 秒一次出來其實沒差；對「長篇生成」「對話回覆」，streaming 跟非 streaming 是兩種等級的體驗。

## 小結

1. **Streaming 讓「等」變得不像「等」**——感知速度勝過實際速度
2. **`stream=True`** 加 **`for event in stream`** 是基本骨架
3. **看 `response.output_text.delta`** 拿增量文字，**`response.completed`** 拿總結資訊
4. **`flush=True`** 必須有，否則被 buffer 吃掉
5. **Streamlit 的 `st.write_stream()`** 完美對接，幾行做出 ChatGPT 體驗
6. **超過 200 字輸出強烈推薦用 streaming**

下一章我們把零散的工具整理成一個正式專案——專案結構、README、`.gitignore`，準備交付給使用者。

## 練習

1. 把 Chapter 8 的摘要工具改成 streaming 版本，比較兩種版本的「感覺」。
2. 在 Streamlit GUI 上加一個「即時摘要」按鈕，用 `st.write_stream()` 顯示。
3. 寫一個簡單的 chatbot 命令列工具：輸入一行、模型 streaming 回應、再輸入下一行。注意：本課沒講對話歷史，可以先不保留歷史，每次當作獨立問題。
4. 故意在 streaming 中途按 Ctrl+C 中止，觀察 Python 怎麼處理（提示：用 try/except 捕捉 `KeyboardInterrupt`）。
