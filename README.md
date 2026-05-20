# Learning OpenAI API with Python

從第一個 API call 到自己的 AI 小工具。共 18 章，O'Reilly 風格中文教材。

## 線上閱讀

`index.html` 是合併版單頁瀏覽，所有章節 + TOC + 章節間導覽集中一頁。

## 本機預覽

直接打開 `index.html` 即可：

```bash
open index.html   # macOS
# 或用 Live Server / 任意靜態 HTTP 伺服器
python3 -m http.server 8000
# 然後瀏覽器打開 http://localhost:8000
```

## 部署到 GitHub Pages

### 方案 A：chapters/ 內容當 repo root（推薦，URL 較乾淨）

```bash
cd chapters
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:你的帳號/openai-api-course.git
git branch -M main
git push -u origin main
```

到 GitHub repo → Settings → Pages → Source 選「main / root」。

幾分鐘後可瀏覽：`https://你的帳號.github.io/openai-api-course/`

### 方案 B：保留資料夾結構

把整個 `note/` 推到 repo，GitHub Pages 設定 Source 為 `main` branch + `/chapters` 資料夾。

URL：`https://你的帳號.github.io/repo名稱/`

## 章節結構

```
chapters/
├── index.html               # 合併單頁版（瀏覽入口）
├── style.css                # 共用樣式
├── build_index.py           # 重新產生 index.html 用
├── ch00_environment_setup.{md,html}
├── ch01_python_syntax_basics.{md,html}
├── ch02_python_files_errors.{md,html}
├── ch03_what_is_api.{md,html}
├── ch04_http_and_json.{md,html}
├── ch05_python_dev_env.{md,html}
├── ch06_first_api_call.{md,html}
├── ch07_prompt_basics.{md,html}
├── ch08_text_tool.{md,html}
├── ch09_speech_to_text.{md,html}
├── ch10_audio_ffmpeg.{md,html}
├── ch11_long_audio_split.{md,html}
├── ch12_streamlit_gui.{md,html}
├── ch13_structured_output.{md,html}
├── ch14_streaming.{md,html}
├── ch15_project_structure.{md,html}
├── ch16_security_cost_errors.{md,html}
└── ch17_final_project.{md,html}
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

## 授權

教材內容請依個人或團體需要使用。範例程式以 MIT 授權釋出。
# openai_api_whisper_tutorial
