# OpenAI API Whisper Tutorial

從 Python 基礎、第一個 OpenAI API call，到語音轉文字、長音檔切分、Streamlit GUI 與完整小工具。共 18 章，採中文教材形式撰寫。

## 線上閱讀

GitHub Pages：

https://g23988.github.io/openai_api_whisper_tutorial/

`index.html` 是合併版單頁瀏覽，包含所有章節、目錄與章節間導覽。

## 適合誰

- 想用 Python 呼叫 OpenAI API 的初學者
- 想把錄音、會議音檔或訪談音檔轉成文字的人
- 想做自己的 AI 文字處理或語音轉文字小工具的人
- 想理解 API key、安全性、成本估算與錯誤處理的人

## 章節

- Chapter 00：環境設定與終端機基礎
- Chapter 01：Python 語法基礎
- Chapter 02：檔案處理與錯誤處理
- Chapter 03：什麼是 API
- Chapter 04：HTTP 與 JSON
- Chapter 05：Python 開發環境與 `OPENAI_API_KEY`
- Chapter 06：第一次 OpenAI API 呼叫
- Chapter 07：Prompt 基礎
- Chapter 08：文字處理工具
- Chapter 09：Speech to Text
- Chapter 10：音訊與 FFmpeg
- Chapter 11：長音檔切分
- Chapter 12：Streamlit GUI
- Chapter 13：Structured Output
- Chapter 14：Streaming
- Chapter 15：專案結構
- Chapter 16：安全、成本與錯誤處理
- Chapter 17：Final Project

## 本機預覽

直接打開 `index.html` 即可：

```bash
open index.html   # macOS
# 或用 Live Server / 任意靜態 HTTP 伺服器
python3 -m http.server 8000
# 然後瀏覽器打開 http://localhost:8000
```

## 檔案結構

```
.
├── index.html              # 合併單頁版，GitHub Pages 入口
├── style.css               # 共用樣式
├── build_index.py          # 重新產生 index.html 用
├── ch00_*.md / .html
├── ...
└── ch17_*.md / .html
```

每章兩個檔：

- `.md` — Markdown 原始版（GitHub 上會自動渲染）
- `.html` — O'Reilly 風格獨立 HTML（Note/Tip/Warning 框、米色背景、襯線字體）

## 修改後重建 index.html

如果改了任一章的 `.html`，跑一次：

```bash
python3 build_index.py
```

會根據各章 HTML 重新組合 `index.html`。

## 部署

這個 repo 使用 GitHub Pages，來源是 `main` branch 的 `/root`。

部署完成後網址為：

https://g23988.github.io/openai_api_whisper_tutorial/

## 授權

教材內容請依個人或團體需要使用。範例程式以 MIT 授權釋出。
