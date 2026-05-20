"""把 chapters/ 底下 18 章 HTML 合併成單頁 index.html。

只抓每章 <article>...</article> 內容，包進 <section id="chXX">，
產生跟 https://g23988.github.io/fastMCP_tutorial/ 類似的單頁瀏覽結構。
"""
import re
from pathlib import Path

CHAPTERS = [
    ("ch00", "ch00_environment_setup.html", "開課前準備"),
    ("ch01", "ch01_python_syntax_basics.html", "Python 小白急救包（一）：語法與資料"),
    ("ch02", "ch02_python_files_errors.html", "Python 小白急救包（二）：檔案與錯誤處理"),
    ("ch03", "ch03_what_is_api.html", "API 是什麼"),
    ("ch04", "ch04_http_and_json.html", "HTTP 與 JSON 基礎"),
    ("ch05", "ch05_python_dev_env.html", "建立 Python 開發環境"),
    ("ch06", "ch06_first_api_call.html", "第一個 Responses API 程式"),
    ("ch07", "ch07_prompt_basics.html", "Prompt 基礎"),
    ("ch08", "ch08_text_tool.html", "做一個文字小工具"),
    ("ch09", "ch09_speech_to_text.html", "Speech to Text"),
    ("ch10", "ch10_audio_ffmpeg.html", "音訊格式與 ffmpeg 基礎"),
    ("ch11", "ch11_long_audio_split.html", "長音檔切段與轉錄"),
    ("ch12", "ch12_streamlit_gui.html", "Streamlit GUI"),
    ("ch13", "ch13_structured_output.html", "Structured Output"),
    ("ch14", "ch14_streaming.html", "Streaming"),
    ("ch15", "ch15_project_structure.html", "專案結構與 README"),
    ("ch16", "ch16_security_cost_errors.html", "安全、成本與錯誤排除"),
    ("ch17", "ch17_final_project.html", "期末專案：會議逐字稿工具"),
]

# 把 18 章分成 5 個 Part（依 openai_api_course_plan.md 的 Part 切分）
PARTS = [
    ("I",   "基礎準備",            range(0, 5)),    # Ch 0-4
    ("II",  "OpenAI API 入門",     range(5, 9)),    # Ch 5-8
    ("III", "音訊與 ffmpeg",       range(9, 12)),   # Ch 9-11
    ("IV",  "圖形化工具與輸出品質", range(12, 15)),  # Ch 12-14
    ("V",   "交付、維護與安全",     range(15, 18)),  # Ch 15-17
]

HERE = Path(__file__).parent


def extract_article(html: str) -> str:
    """抓 <article>...</article> 內容（含標籤之間的東西，不含外層 article 標籤）。"""
    match = re.search(r"<article>(.*?)</article>", html, re.DOTALL)
    if not match:
        raise ValueError("找不到 <article> 區塊")
    return match.group(1).strip()


def extract_inline_style(html: str) -> str:
    """抓 head 裡個別章節定義的 <style> ... </style>（例如 ch04 的 table）。"""
    matches = re.findall(
        r"<style>(.*?)</style>",
        html,
        re.DOTALL,
    )
    return "\n".join(m.strip() for m in matches if m.strip())


def build_toc(chapters) -> str:
    items = []
    for i, (anchor, _, title) in enumerate(chapters):
        chapter_num = "Chapter 0" if i == 0 else f"Chapter {i}"
        items.append(
            f'    <li><a href="#{anchor}">{chapter_num}. {title}</a></li>'
        )
    return "\n".join(items)


def build_sections(chapters) -> tuple[str, str]:
    """回傳 (sections_html, combined_inline_styles)。"""
    sections = []
    extra_styles = set()
    total = len(chapters)
    for i, (anchor, fname, title) in enumerate(chapters):
        html = (HERE / fname).read_text(encoding="utf-8")
        article = extract_article(html)
        style = extract_inline_style(html)
        if style:
            extra_styles.add(style)

        prev_link = ""
        next_link = ""
        if i > 0:
            prev_anchor = chapters[i - 1][0]
            prev_title = chapters[i - 1][2]
            prev_link = f'<a class="nav-prev" href="#{prev_anchor}">← 上一章：{prev_title}</a>'
        if i < total - 1:
            next_anchor = chapters[i + 1][0]
            next_title = chapters[i + 1][2]
            next_link = f'<a class="nav-next" href="#{next_anchor}">下一章：{next_title} →</a>'

        nav = f"""
<div class="chapter-nav">
  {prev_link}
  <a class="nav-top" href="#top">↑ 回目錄</a>
  {next_link}
</div>
""".strip()

        sections.append(
            f'<section id="{anchor}" class="chapter">\n{article}\n{nav}\n</section>'
        )
    return "\n\n".join(sections), "\n".join(sorted(extra_styles))


def build_index():
    toc = build_toc(CHAPTERS)
    sections, extra_styles = build_sections(CHAPTERS)

    # Build sidebar grouped by Part
    sidebar_blocks = []
    for part_num, part_title, idx_range in PARTS:
        items = []
        for i in idx_range:
            anchor, _, title = CHAPTERS[i]
            num = "0" if i == 0 else str(i)
            items.append(
                f'        <li><a href="#{anchor}" data-target="{anchor}">'
                f'<span class="num">Ch {num}</span>'
                f'<span class="ttl">{title}</span></a></li>'
            )
        items_html = "\n".join(items)
        sidebar_blocks.append(
            f'      <div class="part">\n'
            f'        <div class="part-label">'
            f'<span class="part-num">Part {part_num}</span>'
            f'<span class="part-name">{part_title}</span>'
            f'</div>\n'
            f'        <ol>\n{items_html}\n        </ol>\n'
            f'      </div>'
        )
    sidebar_html = "\n".join(sidebar_blocks)

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Learning OpenAI API with Python</title>
<link rel="stylesheet" href="style.css">
<style>
{extra_styles}

/* index page specific */
html {{ scroll-behavior: smooth; scroll-padding-top: 24px; }}

body {{
  max-width: none;
  margin: 0;
  padding: 0;
  background: var(--bg);
}}

.layout {{
  display: grid;
  grid-template-columns: 296px 1fr;
  max-width: 1200px;
  margin: 0 auto;
  align-items: start;
}}

/* === Left sidebar === */
.sidebar {{
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  padding: 44px 18px 48px 36px;
  border-right: 1px solid rgba(0,0,0,0.08);
  background: #fdfcf7;
  font-size: 0.875em;
  line-height: 1.55;
  font-family: Georgia, "Source Han Serif TC", "Noto Serif CJK TC", "PingFang TC", serif;
}}

.sidebar .brand-block {{
  padding: 0 8px;
  margin-bottom: 30px;
  border-bottom: 1px solid rgba(0,0,0,0.07);
  padding-bottom: 22px;
}}
.sidebar .brand {{
  font-family: Georgia, serif;
  font-weight: 700;
  font-size: 0.95em;
  letter-spacing: 0.04em;
  color: #1a1a1a;
  margin: 0;
  line-height: 1.3;
}}
.sidebar .brand-sub {{
  font-size: 0.82em;
  color: #8a8478;
  font-style: italic;
  margin: 3px 0 0;
  letter-spacing: 0.02em;
}}

.sidebar .part {{
  margin-bottom: 22px;
}}
.sidebar .part:last-child {{
  margin-bottom: 0;
}}
.sidebar .part-label {{
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 0 10px;
  margin: 0 0 6px;
  font-family: Menlo, Consolas, monospace;
  font-size: 0.65em;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #9a9183;
}}
.sidebar .part-num {{
  font-weight: 700;
  color: #6b6359;
}}
.sidebar .part-name {{
  font-weight: 600;
  letter-spacing: 0.15em;
}}
.sidebar ol {{
  list-style: none;
  padding: 0;
  margin: 0;
}}
.sidebar li {{
  margin: 0;
}}
.sidebar a {{
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 6px 10px 6px 12px;
  color: #45413c;
  text-decoration: none;
  border-radius: 4px;
  transition: background 0.12s ease, color 0.12s ease;
  line-height: 1.45;
}}
.sidebar a:hover {{
  background: rgba(60,50,35,0.05);
  color: #1a1a1a;
}}
.sidebar a:focus-visible {{
  outline: 2px solid #c0a36a;
  outline-offset: 1px;
}}
.sidebar a.active {{
  background: rgba(60,50,35,0.07);
  color: #111;
  font-weight: 600;
}}
.sidebar .num {{
  flex-shrink: 0;
  min-width: 36px;
  font-family: Menlo, Consolas, monospace;
  font-size: 0.74em;
  color: #a8a092;
  letter-spacing: 0.02em;
  font-weight: 500;
}}
.sidebar a.active .num {{
  color: #555;
}}
.sidebar .ttl {{
  flex: 1;
}}

/* Custom thin scrollbar */
.sidebar::-webkit-scrollbar {{ width: 8px; }}
.sidebar::-webkit-scrollbar-track {{ background: transparent; }}
.sidebar::-webkit-scrollbar-thumb {{
  background: rgba(0,0,0,0.12);
  border-radius: 4px;
  border: 2px solid #fdfcf7;
}}
.sidebar::-webkit-scrollbar-thumb:hover {{
  background: rgba(0,0,0,0.22);
}}
.sidebar {{ scrollbar-width: thin; scrollbar-color: rgba(0,0,0,0.15) transparent; }}

/* === Main content === */
.content {{
  padding: 0 36px;
  max-width: 760px;
}}

.site-header {{
  text-align: left;
  padding: 60px 0 30px;
  border-bottom: 2px solid var(--text);
  margin-bottom: 40px;
}}
.site-header h1 {{
  font-size: 2.2em;
  margin: 0 0 0.3em;
  border: none;
  padding: 0;
  letter-spacing: 0.04em;
}}
.site-header .subtitle {{
  font-size: 1.1em;
  color: var(--muted);
  margin: 0;
  font-style: italic;
}}
.site-header .meta {{
  margin-top: 16px;
  font-size: 0.85em;
  color: var(--muted);
  font-family: Menlo, Consolas, monospace;
}}

/* === Mobile TOC (top, fallback when no sidebar) === */
.toc {{
  background: #f3efe0;
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 24px 32px;
  margin: 2em 0 3em;
}}
.toc h2 {{
  margin: 0 0 0.8em;
  border: none;
  padding: 0;
  font-size: 1.2em;
}}
.toc ol {{ margin: 0; padding-left: 1.6em; }}
.toc li {{ margin: 0.5em 0; line-height: 1.5; }}
.toc a {{
  color: var(--text);
  text-decoration: none;
  border-bottom: 1px dotted var(--muted);
}}
.toc a:hover {{
  color: var(--note-border);
  border-bottom-color: var(--note-border);
}}

.intro {{ margin: 2em 0; }}
.intro p {{ line-height: 1.85; }}

.chapter {{
  margin: 5em 0 4em;
  padding-top: 1em;
  border-top: 1px dashed var(--rule);
}}
.chapter:first-of-type {{ border-top: none; }}

.chapter-nav {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 4em 0 1em;
  padding: 20px 0;
  border-top: 1px solid var(--rule);
  font-size: 0.92em;
  flex-wrap: wrap;
}}
.chapter-nav a {{
  color: var(--note-border);
  text-decoration: none;
  font-family: Menlo, Consolas, monospace;
}}
.chapter-nav a:hover {{ text-decoration: underline; }}
.nav-prev {{ flex: 1; text-align: left; }}
.nav-top  {{ flex: 0; text-align: center; padding: 0 16px; color: var(--muted) !important; }}
.nav-next {{ flex: 1; text-align: right; }}

.back-to-top {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--text);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-size: 1.2em;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  opacity: 0.85;
  transition: opacity 0.2s;
  z-index: 100;
}}
.back-to-top:hover {{ opacity: 1; }}

/* Show top TOC only on mobile (when sidebar hidden) */
.mobile-toc {{ display: none; }}

@media (max-width: 900px) {{
  .layout {{
    display: block;
  }}
  .sidebar {{ display: none; }}
  .content {{ padding: 0 22px; max-width: 760px; margin: 0 auto; }}
  .mobile-toc {{ display: block; }}
  .site-header {{ padding: 40px 0 20px; }}
  .site-header h1 {{ font-size: 1.8em; }}
}}

@media (max-width: 600px) {{
  .site-header h1 {{ font-size: 1.5em; }}
  .toc {{ padding: 18px 22px; }}
  .chapter-nav {{ flex-direction: column; gap: 8px; }}
  .nav-prev, .nav-next, .nav-top {{ text-align: center; flex: none; }}
}}
</style>
</head>
<body>

<a id="top"></a>

<div class="layout">

  <aside class="sidebar">
    <div class="brand-block">
      <p class="brand">Learning OpenAI API</p>
      <p class="brand-sub">with Python · 18 章中文教材</p>
    </div>
{sidebar_html}
  </aside>

  <div class="content">

    <header class="site-header">
      <h1>Learning OpenAI API with Python</h1>
      <p class="subtitle">從第一個 API call 到自己的 AI 小工具</p>
      <p class="meta">18 章 · 中文 · O'Reilly 風格教材</p>
    </header>

    <section class="intro">
      <p>這是一套給 API 初學者的 OpenAI API 實作課。課程不從 AI 理論開始，而是帶學員一步一步做出可以使用的小工具：文字生成、摘要、語音轉文字、音訊轉檔、圖形化介面，以及最後的會議逐字稿工具。</p>

      <p>目標讀者：會基本操作電腦、沒寫過或寫過一點 Python、想知道 ChatGPT 以外如何把 OpenAI 能力接到自己工具裡的人。每章都有可執行範例、可交付的小成果，以及常見錯誤排除。</p>

      <p>建議從 Chapter 0 開始，按章節順序閱讀。每章約 1500 到 2500 字加範例，全部讀完約 4 到 6 小時，動手做完整套大約 8 到 10 週。</p>
    </section>

    <nav class="toc mobile-toc">
      <h2>目錄</h2>
      <ol>
{toc}
      </ol>
    </nav>

    <main>
{sections}
    </main>

  </div>

</div>

<a href="#top" class="back-to-top" aria-label="回到頂端">↑</a>

<script>
  // Scroll-spy: highlight current chapter in sidebar based on scroll position.
  (function () {{
    const links = document.querySelectorAll('.sidebar a[data-target]');
    if (!links.length) return;

    const linkByTarget = {{}};
    links.forEach(a => {{ linkByTarget[a.dataset.target] = a; }});

    const sections = Array.from(document.querySelectorAll('section.chapter'));
    if (!sections.length) return;

    let currentActive = null;

    function setActive(id) {{
      if (currentActive === id) return;
      currentActive = id;
      links.forEach(a => a.classList.remove('active'));
      const link = linkByTarget[id];
      if (link) {{
        link.classList.add('active');
        // Keep active link visible in sidebar if scrolled
        const sidebar = document.querySelector('.sidebar');
        const rect = link.getBoundingClientRect();
        const sidebarRect = sidebar.getBoundingClientRect();
        if (rect.top < sidebarRect.top || rect.bottom > sidebarRect.bottom) {{
          link.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
        }}
      }}
    }}

    const observer = new IntersectionObserver((entries) => {{
      // Pick the section closest to the top edge of the viewport that's visible.
      const visible = entries
        .filter(e => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible.length) {{
        setActive(visible[0].target.id);
      }}
    }}, {{
      rootMargin: '-10% 0px -70% 0px',
      threshold: 0,
    }});

    sections.forEach(s => observer.observe(s));

    // Initialize with first section
    setActive(sections[0].id);
  }})();
</script>

</body>
</html>
"""

    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(f"已產生 {HERE / 'index.html'}")


if __name__ == "__main__":
    build_index()
