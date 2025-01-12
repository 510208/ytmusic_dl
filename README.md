# ytmusic_dl - YouTube 音樂下載器

`ytmusic_dl` 是一個基於 Python 的命令列工具，用於從 YouTube 下載音樂並自動添加 ID3 標籤 (包含專輯封面)。它支援下載單一歌曲和整個播放清單，並具有方便的剪貼簿監聽模式。

## 功能

*   **下載單曲:** 從 YouTube 影片連結下載音訊。
*   **下載播放清單:** 從 YouTube 播放清單連結下載所有歌曲。
*   **監聽模式:** 自動監聽剪貼簿，當偵測到 YouTube 連結時自動下載。
*   **ID3 標籤:** 自動為下載的 MP3 檔案添加 ID3 標籤，包括標題、歌手和專輯封面。
*   **ID3 標籤版本選擇:** 可以選擇使用最新的 ID3v2.4 或較舊的 ID3v2.3 標籤格式 (預設為 ID3v2.3)。
*   **格式轉換:** 自動將下載的 M4A 檔案轉換為 MP3。
*   **進度條:** 顯示下載進度。
*   **桌面通知 (可選):** 在監聽模式下提供桌面通知，即時更新下載狀態 (僅限 Windows 10)。
*   **平行下載:** 下載播放清單時支援多執行緒平行下載，加速下載速度。

## 安裝

### 前置要求

1. **Python 3:** 建議使用 Python 3.7 或更高版本。
2. **ffmpeg:**  需要安裝 ffmpeg 並將其添加到系統路徑 (PATH) 中。可以從 [ffmpeg 官網](https://ffmpeg.org/download.html) 下載並按照說明安裝。 
    > 注意：本程式已將 `ffmpeg.exe` 的環境路徑部分註解掉，若您確認已將 `ffmpeg` 加入系統路徑中，則不必修改 `main.py` 檔案。

### 安裝步驟

1. **下載專案:**

    ```bash
    git clone <repository_url>
    cd ytmusic_dl
    ```

    或直接從 GitHub 下載 ZIP 檔案並解壓縮。

2. **建立虛擬環境 (建議):**

    ```bash
    python3 -m venv .venv
    ```

3. **啟用虛擬環境:**

    *   **Windows:**

        ```bash
        .venv\Scripts\activate
        ```

    *   **macOS/Linux:**

        ```bash
        source .venv/bin/activate
        ```

4. **安裝依賴:**

    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

### 命令列介面

程式主要透過命令列介面進行操作。以下是主要的指令和選項：

```bash
python main.py [OPTIONS] COMMAND [ARGS]...
```

**全域選項:**

*   `--debug`, `-d`: 開啟除錯模式，輸出更詳細的日誌資訊。

**指令:**

*   **`single`:** 下載單首歌曲。
*   **`list`:** 下載播放清單。
*   **`listen`:** 啟動剪貼簿監聽模式。

### 下載單曲

```bash
python main.py single -l <youtube_video_url> [OPTIONS]
```

**選項:**

*   `-l`, `--uri`:  **必填**，YouTube 影片網址。
*   `-o`, `--output`: 輸出資料夾，預設為當前目錄。
*   `-n`, `--noid3`: 不添加 ID3 標籤資訊。
*   `-i`, `--id3_latest`: 使用最新的 ID3v2.4 標籤格式 (預設為 ID3v2.3)。

**範例:**

```bash
python main.py single -l "https://www.youtube.com/watch?v=XXXXXXXXXXX" -o "MyMusic"
```

### 下載播放清單

```bash
python main.py list -l <youtube_playlist_url> [OPTIONS]
```

**選項:**

*   `-l`, `--uri`:  **必填**，YouTube 播放清單網址。
*   `-o`, `--output`: 輸出資料夾，預設為當前目錄。將在輸出資料夾下建立以播放清單名稱命名的子資料夾。
*   `-n`, `--noid3`: 不添加 ID3 標籤資訊。
*   `-i`, `--id3_latest`: 使用最新的 ID3v2.4 標籤格式 (預設為 ID3v2.3)。
*   `-m`, `--parallel_max`: 最大平行下載數，預設為 5。

**範例:**

```bash
python main.py list -l "https://www.youtube.com/playlist?list=PLXXXXXXXXXXXX" -o "MyPlaylists" -m 10
```

### 監聽模式

```bash
python main.py listen [OPTIONS]
```

**選項:**

*   `-n`, `--no-notifaction`: 關閉桌面通知 (預設開啟)。

**範例:**

```bash
python main.py listen
```

啟動監聽模式後，程式會持續監聽剪貼簿。當偵測到 YouTube 影片或播放清單連結時，會自動開始下載。

**退出監聽模式:** 在終端機中按下 `Ctrl + C`。

## 注意事項

*   使用最新的 ID3v2.4 標籤格式可能會導致某些播放器無法正確顯示專輯封面或歌手等資訊。已知 Windows 檔案總管、Windows Media Player 以及 Windows 內建的媒體播放器可能會有此問題。建議使用 VLC、foobar2000、AIMP 等播放器，或移除 `-i` 旗標以使用較舊的 ID3v2.3 標籤格式。
*   請確保您已安裝 `ffmpeg`，並將其正確設定到環境變數 `PATH` 中。
*   `listen` 指令中的桌面通知功能依賴 `win10toast` 函式庫，僅適用於 Windows 10 系統。

## 錯誤排除

*   如果遇到下載錯誤，請先檢查網路連線和 YouTube 連結是否正確。
*   可以使用 `-d` 選項開啟除錯模式，查看更詳細的錯誤資訊。
*   如果程式運行時沒有回應，可以嘗試在執行指令前先加入 `python -u` 參數

## 使用許可

本專案使用 MIT 許可證。詳情請參閱 `LICENSE` 檔案。

## 貢獻

歡迎提交 Issue 或 Pull Request 來幫助改進這個專案。

## 作者

SamHacker
