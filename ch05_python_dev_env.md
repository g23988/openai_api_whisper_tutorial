# Chapter 5. 建立 Python 開發環境

前面四章我們把所有概念基礎鋪好了。從這章開始，每一章都會真的寫程式、真的跑東西。但在第一通 API call 之前，我們得先把工作環境準備好。

這章要做四件事：

1. 建立一個專案資料夾
2. 在裡面建立 Python 虛擬環境
3. 安裝 OpenAI SDK
4. 安全地設定 `OPENAI_API_KEY`

整個流程大概十分鐘——但走錯一步，後面九個章節都會卡住。所以慢一點、確認每一步。

## 為什麼要用虛擬環境

很多人第一次學 Python 會直接：

```bash
pip install openai
```

然後就跑了。短期看起來沒問題。長期會出事。

問題是：**你電腦上的 Python 只有一個，但你會做的專案不只一個**。

想像一下情境：

- 你今年用 OpenAI SDK 1.50 做了一個會議逐字稿工具
- 明年你接到一個新案子，要用 OpenAI SDK 2.0（這個版本改了 API）
- 結果你升級了 SDK，去年的工具直接壞掉

或者更可怕的情境：

- 你的工作環境用 `numpy 1.x`
- 你裝了一個套件 A，它要求 `numpy 2.x`
- A 升級了 numpy，於是你原本的程式 B 全部炸掉

這就是 Python 圈很有名的「**dependency hell**」——套件之間版本互相衝突，東動西動就壞。

**虛擬環境的解法是：每個專案有自己獨立的 Python 跟自己的套件**。專案 A 用 SDK 1.50、專案 B 用 SDK 2.0，井水不犯河水。

> **Tip** — Python 不是唯一被 dependency hell 折磨的語言——Node.js、Ruby、Java 都有過類似問題，後來各自演化出 npm 的 <code>node_modules/</code>、Ruby 的 <code>Bundler</code>、Java 的 <code>Maven</code>。Python 的 <code>venv</code> 在 2012 年（Python 3.3）被收進標準庫，從此「每個專案一個 venv」變成不成文的規矩。早期還有 <code>virtualenv</code>、<code>conda</code>、<code>poetry</code>、<code>uv</code> 等競爭工具，但對本課這種規模的專案，內建的 <code>venv</code> 完全夠用。

## 建立專案資料夾

打開終端機，進到你想放專案的位置（例如桌面）：

```bash
cd ~/Desktop
```

建立資料夾並進去：

```bash
mkdir openai-course
cd openai-course
```

確認你現在在正確位置：

```bash
pwd
```

應該看到類似 `/Users/你的名字/Desktop/openai-course`（macOS）或 `C:\Users\你的名字\Desktop\openai-course`（Windows）。

## 建立虛擬環境

```bash
python3 -m venv .venv
```

這行做的事：用 Python 內建的 `venv` 模組，建立一個名為 `.venv` 的資料夾，裡面是一個獨立的 Python 環境。

> **Note** — 為什麼資料夾叫 <code>.venv</code>（前面有個點）？因為 macOS / Linux 上，檔名開頭是 <code>.</code> 的檔案會被當成「隱藏檔」，預設不顯示。把虛擬環境設成隱藏可以讓你的專案資料夾看起來乾淨——畢竟 venv 裡面有上千個檔案，你不會想常看到。<code>.venv</code> 是社群最常見的命名，也是 VS Code、PyCharm 預設會偵測的名稱。

跑 `ls -la`（macOS）或 `dir`（Windows）你會看到 `.venv` 資料夾已經建好。

## 啟動虛擬環境

虛擬環境建好之後，要「啟動」它才會生效。

**macOS / Linux：**

```bash
source .venv/bin/activate
```

**Windows（PowerShell）：**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows（cmd）：**

```cmd
.venv\Scripts\activate.bat
```

啟動成功的話，終端機提示符前面會多一個 `(.venv)`，像這樣：

```text
(.venv) wei@MacBook openai-course %
```

這個 `(.venv)` 是個提醒——告訴你「你現在在虛擬環境裡」。要關掉的話打：

```bash
deactivate
```

> **Warning** — <strong>每次新開終端機都要重新 <code>activate</code></strong>。這是新手最常踩的坑：上次跑得好好的，今天打開終端機跑 <code>python myapp.py</code> 卻說「找不到 openai 套件」——通常都是因為忘記 activate。看到 <code>(.venv)</code> 就是啟動了，沒看到就是沒啟動。

確認 Python 來自虛擬環境：

```bash
which python   # macOS / Linux
where python   # Windows
```

應該看到路徑是 `.../openai-course/.venv/bin/python`（macOS）或類似的 Windows 路徑。

## 安裝 OpenAI SDK

啟動虛擬環境之後，安裝套件：

```bash
pip install openai
```

`pip` 是 Python 的套件管理器。它會去 PyPI（Python Package Index，套件的中央倉庫）下載 `openai` 套件並裝到當前的虛擬環境裡。

跑完之後可以確認：

```bash
pip show openai
```

應該看到版本號跟其他資訊。**沒看到的話一定是沒啟動虛擬環境**——回去確認終端機前面有沒有 `(.venv)`。

順便裝幾個本課後面會用到的套件：

```bash
pip install python-dotenv
```

`python-dotenv` 讓我們用 `.env` 檔管理環境變數（下一節馬上會用到）。

## 把已裝套件記下來

寫一個檔案 `requirements.txt`，記錄這個專案用到的套件：

```bash
pip freeze > requirements.txt
```

打開 `requirements.txt` 你會看到類似：

```text
openai==1.50.0
python-dotenv==1.0.0
...
```

**這個檔案很重要**：未來別人（或你自己換電腦）要跑你的專案時，只要：

```bash
pip install -r requirements.txt
```

就會把所有套件裝回來，**版本完全一致**。本課所有專案都會有 `requirements.txt`。

## 設定 OPENAI_API_KEY

到 [platform.openai.com](https://platform.openai.com) 註冊帳號（如果還沒有），到 API keys 頁面建立一把新的 key。複製下來——**這個 key 只會顯示一次**，關掉就找不到了，要重新建。

接下來重點是：**不要把 key 寫進程式碼**。我們用 `.env` 檔案。

在專案資料夾建立 `.env`：

```bash
touch .env    # macOS / Linux
```

或者在編輯器裡新建一個檔案叫 `.env`。

打開來寫一行：

```text
OPENAI_API_KEY=sk-proj-你的key貼這裡
```

**注意：等號兩邊不要有空格，key 不要加引號**。

接著在 Python 程式裡這樣讀：

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
```

`load_dotenv()` 會把 `.env` 裡的內容讀進「環境變數」，然後 `OpenAI()` 預設會去環境變數找 `OPENAI_API_KEY`，剛好對接。

> **Tip** — 為什麼這層曲折？為什麼不直接 <code>OpenAI(api_key="sk-...")</code>？因為**程式碼跟祕密應該分開**。程式碼會被 git commit、會被 push 到 GitHub、會被同事看到；但 <code>.env</code> 不會（下一步馬上設定）。這樣同一份程式碼可以給多人用，每個人用自己的 key，互不干擾。

## 把 .env 排除在 git 之外

如果你打算用 git 管版本（強烈建議），務必建立 `.gitignore`：

```text
.venv/
.env
__pycache__/
*.pyc
.DS_Store
transcripts/
uploads/
```

`.gitignore` 是給 git 看的「請忽略這些檔案」清單。**這個動作必須在第一次 commit 之前做**——一旦 `.env` 進了 git 歷史，就算之後刪掉也找得回來，等於洩漏。

> **Warning** — GitHub 上每天都有人把 API key 直接 commit 上去，OpenAI 的 bot 會在幾分鐘內偵測到並撤銷那把 key。<strong>但 bot 不總是夠快</strong>——已經有真實案例是 key 在被撤銷前的幾分鐘內被人撿去打了幾百美金的 API。<code>.gitignore</code> 是免費的保險，務必設定。

## 確認整個環境通了

寫一個 `test_setup.py`：

```python
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("找不到 OPENAI_API_KEY，請確認 .env 檔案")
    exit(1)

client = OpenAI()
print("Client 建立成功")
print(f"OpenAI SDK version: {client._version if hasattr(client, '_version') else 'unknown'}")
```

跑：

```bash
python test_setup.py
```

看到 `Client 建立成功` 就代表所有設定都通了。下一章我們就要打第一通真的 API call。

## 小結

這章設定的事：

1. **建立專案資料夾**：`openai-course/`
2. **建立虛擬環境**：`python3 -m venv .venv`
3. **啟動虛擬環境**：`source .venv/bin/activate`（macOS）或 `.venv\Scripts\activate`（Windows）
4. **安裝套件**：`pip install openai python-dotenv`
5. **記錄相依套件**：`pip freeze > requirements.txt`
6. **設定 API key**：寫進 `.env`，用 `load_dotenv()` 讀
7. **保護 key**：建立 `.gitignore`，把 `.env` 跟 `.venv/` 排除

**每次新開終端機要記得重新 activate**——這是接下來九個章節最容易忘記、最容易卡住的事。

## 練習

1. 把整個流程跑一次，最後跑 `test_setup.py` 確認通了。
2. 把終端機關掉，重新打開，**不**啟動虛擬環境直接跑 `python test_setup.py`，看會跳什麼錯。然後 `activate` 之後再跑一次。
3. 看一下 `requirements.txt` 的內容，跟你裝的套件對得起來嗎？
4. 試試把 `.env` 的內容隨便改錯（例如把 key 改一個字），跑 `test_setup.py`，看會發生什麼。
