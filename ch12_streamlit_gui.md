# Chapter 12. Streamlit GUI

到上一章為止，我們的工具都是命令列程式。對工程師很方便，但**給不會用終端機的同事或家人，沒人會用**。

這章我們把上一章的長音檔轉錄器加上一個圖形介面：可以拖曳上傳、按按鈕、看進度條、下載結果。用的工具叫 **Streamlit**——學完這章你會發現「做出 GUI」竟然這麼簡單。

## 為什麼選 Streamlit

Python 圈做 GUI 的選擇多到嚇人：Tkinter、PyQt、wxPython、Kivy、Flask、Django、FastAPI + 前端...

**Streamlit** 在 2019 年出現，專門為「資料科學家跟 AI 工程師」設計，理念是：

> 你只寫 Python，不寫 HTML、CSS、JavaScript。每個 Python 變數的變化會自動反映在介面上。

聽起來像魔法，但實際就是這樣。

> **Tip** — Streamlit 在 2020-2022 年爆紅，因為它剛好趕上 AI 工具的浪潮——每個會用 Python 跑模型的人，都需要一個快速做 demo 的方式。2022 年 Snowflake（雲端資料平台）以 8 億美金併購 Streamlit，但工具本身依然開源免費。**對「我寫一個 Python 腳本，希望給沒寫過程式的人用」這個情境，沒有比 Streamlit 更省事的工具**。如果你的需求是「正式產品的網頁」「複雜互動」「多人協作」，那 Streamlit 不夠——這時改用 React + FastAPI 比較對。但本課的工具規模 Streamlit 完美。

## 安裝 Streamlit

```bash
pip install streamlit
```

跑一個內建範例確認裝好了：

```bash
streamlit hello
```

瀏覽器會自動開啟一個本機網頁。看到 Streamlit 的歡迎頁就代表 OK。要關掉的話在終端機按 `Ctrl + C`。

## 第一個 Streamlit 程式

建立檔案 `app.py`：

```python
import streamlit as st

st.title("我的第一個 Streamlit 程式")
st.write("這是一段 Markdown 內容")

name = st.text_input("你叫什麼名字？")
if name:
    st.write(f"哈囉，{name}！")
```

執行：

```bash
streamlit run app.py
```

瀏覽器會打開一個頁面，有標題、文字、輸入框。在輸入框打字後，下面會即時顯示「哈囉，xxx」。

你可能會問：「我哪一行寫了「監聽輸入變化」？哪一行寫了「重新渲染畫面」？」

答案是：**沒有**。Streamlit 的核心魔法是：**每次你在介面上做任何互動，整個腳本會從頭跑一次**。`text_input` 第一次跑時 `name` 是空字串，所以下面的 `if name` 不成立。你打字之後腳本再跑一次，`name` 有值，所以顯示「哈囉」。

這個「每次重跑」的模型超級反直覺，但反而讓你**完全用 Python 思考**——沒有「事件處理」「狀態同步」這些前端工程師的痛點。

## 重做轉錄工具的 GUI

上一章的 `transcribe_long.py` 是命令列版本。我們把同樣的能力包成 GUI：

```python
# app.py
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="會議逐字稿工具", page_icon=None)
st.title("會議逐字稿工具")

uploaded = st.file_uploader(
    "上傳音檔",
    type=["mp3", "mp4", "m4a", "wav", "webm", "ogg", "flac"],
)

model = st.selectbox(
    "選擇轉錄模型",
    ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"],
    index=0,
)

language = st.selectbox("語言", ["zh", "en", "ja"], index=0)

if uploaded and st.button("開始轉錄"):
    # 把上傳的檔案存到暫存路徑
    temp_path = Path("uploads") / uploaded.name
    temp_path.parent.mkdir(exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    # 顯示進度
    with st.spinner("轉錄中..."):
        client = OpenAI()
        with open(temp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model=model,
                file=f,
                language=language,
            )

    st.success("完成")
    st.text_area("逐字稿", result.text, height=400)
    st.download_button(
        "下載 .txt",
        data=result.text,
        file_name=f"{temp_path.stem}.txt",
        mime="text/plain",
    )
```

跑：

```bash
streamlit run app.py
```

打開瀏覽器，你會看到：

- 標題
- 上傳音檔的拖曳區
- 模型下拉選單
- 語言下拉選單
- 「開始轉錄」按鈕
- 轉錄中的旋轉指示
- 結果文字框
- 下載按鈕

**這就是一個完整的 GUI 工具了**，不到 50 行 Python。

## Streamlit 常用元件

幾個你會反覆用到的：

```python
st.title("大標題")
st.header("中標題")
st.subheader("小標題")
st.write("一般文字，支援 Markdown")
st.markdown("**粗體** *斜體* `程式碼`")
st.code("print('hello')", language="python")

# 輸入元件
name = st.text_input("文字")
age = st.number_input("數字", min_value=0, max_value=120)
agreed = st.checkbox("同意條款")
mood = st.radio("心情", ["好", "普通", "差"])
country = st.selectbox("國家", ["TW", "JP", "US"])
tags = st.multiselect("標籤", ["重要", "急", "一般"])
date = st.date_input("日期")
file = st.file_uploader("檔案")

# 動作
if st.button("執行"):
    ...

# 顯示
st.success("成功")
st.warning("警告")
st.error("錯誤")
st.info("資訊")
st.spinner("處理中...")  # 配合 with 使用

# 排版
col1, col2 = st.columns(2)
with col1:
    st.write("左邊")
with col2:
    st.write("右邊")
```

這幾個就能組合出 90% 的工具介面。

## 進度顯示

長任務（轉錄、批次處理）需要進度提示。三種常見做法：

**1. `st.spinner`**——簡單的旋轉指示：

```python
with st.spinner("處理中..."):
    do_long_task()
```

**2. `st.progress`**——進度條：

```python
progress = st.progress(0)
for i, item in enumerate(items):
    process(item)
    progress.progress((i + 1) / len(items))
```

**3. `st.status`**——可展開的狀態框：

```python
with st.status("分段轉錄中...", expanded=True) as status:
    for i, seg in enumerate(segments, 1):
        st.write(f"段 {i}/{len(segments)}：{seg.name}")
        transcribe(seg)
    status.update(label="完成", state="complete")
```

對本課的長音檔轉錄工具來說，`st.status` 最適合——可以看到每段進度，又可以折疊起來。

> **Note** — 進度顯示在 GUI 工具裡幾乎是必備的。沒有進度的話，使用者按下按鈕後盯著畫面，30 秒後可能就以為當機了。**對任何超過 5 秒的操作，都要顯示進度**。這是 UX 的基本禮貌。

## API key 怎麼處理

GUI 版本有個新問題：**API key 從哪來？**

幾種選擇：

**A. 從 `.env` 讀（單人使用）**

```python
load_dotenv()
client = OpenAI()
```

優點：簡單。缺點：給別人用的時候別人得自己改 `.env`。

**B. 用 Streamlit secrets（部署用）**

建立 `.streamlit/secrets.toml`：

```toml
OPENAI_API_KEY = "sk-..."
```

讀法：

```python
import streamlit as st
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
```

優點：部署到 Streamlit Cloud 時內建支援。缺點：本機開發要另設。

**C. 讓使用者自己貼 key（最彈性）**

```python
api_key = st.text_input("OpenAI API Key", type="password")
if api_key:
    client = OpenAI(api_key=api_key)
```

`type="password"` 會把輸入隱藏成 `••••••`。**這是給別人用、又不想付他們 API 費用的最佳方案**。

> **Warning** — 如果你做的 GUI 工具會給別人用、又用方案 B 把你的 key 寫在 <code>secrets.toml</code>，<strong>別人會用你的 key 花你的錢</strong>。不是技術問題，是商業判斷——你願不願意贊助使用者的用量。本課的工具偏向「給每個人自己用」，所以推薦方案 A（個人）或 C（給朋友）。

## 把它全部整合

完整的 GUI 版會議逐字稿工具：

```python
# app.py
import streamlit as st
from pathlib import Path
from openai import OpenAI

st.set_page_config(page_title="會議逐字稿工具", layout="centered")
st.title("會議逐字稿工具")

with st.sidebar:
    st.header("設定")
    api_key = st.text_input("OpenAI API Key", type="password")
    model = st.selectbox(
        "轉錄模型",
        ["gpt-4o-transcribe", "gpt-4o-mini-transcribe", "whisper-1"],
    )
    language = st.selectbox("語言", ["zh", "en", "ja"], index=0)

uploaded = st.file_uploader(
    "上傳音檔（mp3 / mp4 / wav / m4a 等）",
    type=["mp3", "mp4", "m4a", "wav", "webm", "ogg", "flac"],
)

if uploaded and api_key and st.button("開始轉錄"):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    temp_path = upload_dir / uploaded.name
    temp_path.write_bytes(uploaded.getbuffer())

    size_mb = temp_path.stat().st_size / (1024 * 1024)
    st.info(f"檔案大小：{size_mb:.1f} MB")

    if size_mb > 25:
        st.error("檔案超過 25 MB，請改用命令列工具的分段轉錄（Chapter 11）")
        st.stop()

    with st.spinner("轉錄中，請耐心等候..."):
        client = OpenAI(api_key=api_key)
        with open(temp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model=model, file=f, language=language,
            )

    st.success("轉錄完成")
    st.text_area("逐字稿", result.text, height=400)
    st.download_button(
        "下載 .txt",
        data=result.text,
        file_name=f"{temp_path.stem}.txt",
        mime="text/plain",
    )
elif not api_key:
    st.info("請在側邊欄輸入 API Key")
```

這個版本：

- API key 從側邊欄輸入，隱藏顯示
- 模型、語言可選
- 顯示檔案大小，超過 25MB 提醒去用命令列分段版
- 旋轉指示顯示處理中
- 完成後顯示逐字稿，提供下載

跑：

```bash
streamlit run app.py
```

打開瀏覽器，你會看到一個功能完整的工具。可以分享給同事、家人、自己用。

## 小結

1. **Streamlit 是 Python 寫 GUI 最快的工具**——10 分鐘做出第一個工具
2. **核心模型**：每次互動，整個腳本從頭跑一次。反直覺但簡單
3. **常用元件**：`text_input`, `selectbox`, `file_uploader`, `button`, `spinner`, `status`, `download_button`
4. **進度顯示是必備**——超過 5 秒的操作都要有
5. **API key 三種處理方式**——依「給誰用、誰付費」決定

下一章我們學「結構化輸出」——讓模型輸出固定格式的 JSON，下下章把這個 GUI 升級成「轉錄 + 摘要 + Action Items」的完整會議紀錄工具。

## 練習

1. 把這個 GUI 跑起來，用一個短音檔測試完整流程。
2. 加一個「temperature」滑桿（`st.slider("Temperature", 0.0, 1.0, 0.3)`），讓使用者調整。
3. 改成「批次模式」：可以一次上傳多個檔案，依序處理。
4. 加上「最近處理過的檔案」歷史記錄（提示：把結果存到 session state `st.session_state.history = []`）。
