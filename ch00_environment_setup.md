# Chapter 0. 開課前準備

這章不教 API、不寫 Python，只做一件事：確認你的電腦準備好了。

聽起來不重要，但我教課這幾年發現，一半的學員卡關不是因為程式難，而是因為「terminal 找不到、虛擬環境啟動不了、ffmpeg 沒裝、檔案存在桌面但程式說找不到」。這些不是寫程式的問題，是「電腦怎麼操作」的問題。所以這章我們先把這層處理掉，後面才能安心寫程式。

## 為什麼一定要用終端機

很多人第一次看到終端機（Terminal、命令提示字元）那個黑底白字的東西，會問：「我用 GUI（圖形介面）不行嗎？」

可以，但會非常累。

GUI 一次只能做一件事：你點開一個資料夾、點開一個檔案、按一個按鈕。如果你要對 100 個音檔做同樣的處理，你得點 100 次。但終端機讓你寫一行指令就跑完——這不只是省時間，是讓你能把工具「自動化」起來。

我們這套課要做的事——呼叫 API、轉檔案、跑腳本——本質上都是「給電腦一連串指令」。GUI 工具會把這些指令藏起來、包裝成漂亮的按鈕，但學寫程式的時候反而是阻礙。直接面對指令，反而最快。

所以這章我們會用到的指令很少——只有三個。但這三個你要會背。

## pwd, ls, cd

打開終端機（macOS 在「應用程式 → 工具程式 → 終端機」，Windows 推薦用 PowerShell 或 Windows Terminal）。

第一個指令：

```bash
pwd
```

`pwd` 是 "print working directory" 的縮寫，意思是「印出我現在在哪個資料夾」。終端機跟 Finder/檔案總管不一樣——它任何時候都「站在」某個資料夾裡，所有操作都是相對這個位置發生的。如果你不知道自己在哪，所有後續操作都會出問題。

第二個：

```bash
ls
```

`ls` 是 "list" 的縮寫，意思是「列出這個資料夾裡有什麼」。Windows 上對應的指令是 `dir`，但 PowerShell 也認 `ls`。

第三個：

```bash
cd Desktop
```

`cd` 是 "change directory"，意思是「換到另一個資料夾」。`cd Desktop` 會進到名為 `Desktop` 的子資料夾，`cd ..` 會回上一層，`cd ~` 會回到你的家目錄（home directory）。

> **Tip** — `~`（波浪號）在大部分終端機都代表「家目錄」，也就是你登入帳號的根資料夾。在 macOS 是 `/Users/你的帳號名`，在 Windows 是 `C:\Users\你的帳號名`。記住這個符號，後面很多範例會用到。

光是這三個指令，就能讓你在終端機裡走來走去、看清楚自己在哪、有什麼檔案。這已經足夠完成本課所有操作。

## 絕對路徑與相對路徑

這是新手最常踩的坑：你寫了一段程式說「讀取 `meeting.mp3`」，結果程式說「找不到檔案」，但你明明看到那個檔案就在桌面上。

問題通常是路徑。

電腦的檔案有兩種寫法：

**絕對路徑**是從硬碟最頂端開始寫的完整位置，例如：

```text
/Users/wei/Desktop/meeting.mp3
```

不管你在哪裡執行程式，這個路徑都指向同一個檔案。

**相對路徑**是從「你目前在哪個資料夾」算起的位置，例如：

```text
meeting.mp3
```

如果你在 `Desktop` 資料夾裡執行程式，這會找到 `Desktop/meeting.mp3`；但如果你在 `Documents` 資料夾裡，就會找不到，因為 `Documents/meeting.mp3` 不存在。

> **Note** — 當程式說「找不到檔案」，第一件事永遠是跑 `pwd` 確認你目前在哪，然後跑 `ls` 確認那個檔案是不是真的在這個資料夾裡。八成的「找不到檔案」問題都是路徑問題，不是程式 bug。

## 副檔名的小坑（特別給 Mac 使用者）

macOS 預設會把常見副檔名（`.txt`、`.mp3`、`.pdf`）隱藏起來，這在 Finder 裡看起來很美，但對寫程式來說是地雷。

你在 Finder 看到一個檔案叫 `meeting`，實際上它可能叫 `meeting.mp3`，也可能叫 `meeting.mp3.txt`（如果你不小心改副檔名又沒注意）。程式只認真實檔名，所以這時候你會卡住。

請打開 Finder 的偏好設定，把「顯示所有檔名副檔名」打勾。Windows 的檔案總管也有類似的選項（檢視 → 副檔名）。**強烈建議現在就去設定**，否則之後絕對會踩到。

## 確認三個工具

接下來確認本課要用的三個東西都裝好了。

### Python

```bash
python3 --version
```

應該看到類似 `Python 3.11.5` 或 `Python 3.12.x` 的字樣。本課需要 Python 3.10 以上，越新越好。

> **Note** — macOS 跟 Linux 上要打 `python3`，**不是** `python`。這是有歷史原因的：Python 在 2008 年從 2 版升級到 3 版的時候，兩個版本不完全相容，社群花了超過十年才把所有套件遷移過去。為了避免「打 `python` 結果跑出 Python 2 把程式跑壞」的混亂，現代 macOS 跟很多 Linux 發行版直接把 `python` 留給舊版（甚至完全拿掉），新版只能用 `python3`。Windows 因為沒有預裝 Python，所以你裝的就是 3 版，打 `python` 也通常 OK。

### pip

```bash
pip --version
```

或者：

```bash
pip3 --version
```

`pip` 是 Python 的套件管理工具，等下安裝 OpenAI SDK 要用。看到版本號就 OK，看到 `command not found` 就要回頭裝 Python。

### ffmpeg

```bash
ffmpeg -version
```

`ffmpeg` 是處理音訊與影片的瑞士刀。我們在 Chapter 9 到 Chapter 11 處理音檔的時候會大量用到。

如果跳出 `command not found`，要先裝。macOS 推薦用 Homebrew：

```bash
brew install ffmpeg
```

Windows 可以從 [ffmpeg.org](https://ffmpeg.org/download.html) 下載，或者用 Chocolatey/Scoop 之類的套件管理器。

> **Tip** — ffmpeg 這個工具來頭很大。它是 2000 年由一位法國工程師 Fabrice Bellard 寫的開源專案（這人後來還寫了 QEMU 跟 JSLinux），二十多年來幾乎所有處理音訊影像的軟體背後都用它——YouTube、VLC、OBS、瀏覽器播放器全都靠它編解碼。當你聽到「業界標準工具」，ffmpeg 是少數真的當之無愧的那種。

## 平台差異速查表

本課大部分指令在三個平台都一樣，但有幾個常見差異要知道：

| 動作 | macOS / Linux | Windows |
|---|---|---|
| Python 指令 | `python3` | `python` |
| 列出檔案 | `ls` | `dir` 或 `ls`（PowerShell） |
| 顯示環境變數 | `echo $OPENAI_API_KEY` | `echo %OPENAI_API_KEY%`（cmd）或 `echo $env:OPENAI_API_KEY`（PowerShell） |
| 啟動虛擬環境 | `source .venv/bin/activate` | `.venv\Scripts\activate` |
| 家目錄符號 | `~` | `~`（PowerShell）或 `%USERPROFILE%`（cmd） |

> **Warning** — 終端機關掉之後，環境變數會消失。如果你下一章設定的 `OPENAI_API_KEY` 在新的終端機視窗失效了，這是正常的——後面 Chapter 5 會教怎麼讓它永久生效。

## 小結

這章完成的事：

1. 知道終端機是什麼、為什麼要用
2. 會用 `pwd`、`ls`、`cd` 三個指令
3. 知道絕對路徑與相對路徑的差別
4. 確認本機有可用的 Python、pip、ffmpeg
5. 打開檔案副檔名顯示（如果之前沒開）

下一章開始我們會碰真正的程式碼——但不是 OpenAI API，是 Python 自己。要呼叫 API，得先有基本的 Python 手感。

## 練習

1. 打開終端機，跑 `pwd`，把結果寫下來。然後 `cd ~`、再 `pwd`，看看差別。
2. 用 `cd` 進到桌面（macOS：`cd ~/Desktop`；Windows：`cd $env:USERPROFILE\Desktop`），然後 `ls` 看看桌面上有什麼。
3. 建立一個叫 `openai-course` 的資料夾，並 `cd` 進去。提示：用 `mkdir openai-course`。
4. 跑 `python3 --version`、`pip --version`、`ffmpeg -version`，三個都要有版本號出來。如果有任何一個失敗，先解決再進下一章。
