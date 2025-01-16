# YouTUbe音樂下載器，使用pytube、與click，並透過eyed3加入專輯封面
# 作者：SamHacker

# 引入模組
# Click 是一個 Python 模組，用於快速創建命令行界面
import click
# os 模組提供了許多與作業系統互動的函數
import os
# sys 模組提供了與 Python 解釋器和其環境的互動
import sys
# time 模組提供了各種時間相關的函數
import time
# requests 模組允許您發送 HTTP/1.1 請求
import requests
# pytubefix 是一個 YouTube 下載器，支援下載單一影片、播放清單，它是用以取代 pytube 的一個分支
from pytubefix import YouTube, Playlist, Stream   # 引入 YouTube、Playlist、Stream 類別，用於下載影片
from pytubefix.cli import on_progress             # 引入 on_progress 函數，用於顯示下載進度條
from pytubefix.exceptions import PytubeFixError   # 引入 PytubeFixError 類別，用於處理錯誤
from pytubefix.exceptions import VideoUnavailable, BotDetection, VideoPrivate, MembersOnly, VideoRegionBlocked, LoginRequired, AgeRestrictedError    # 引入錯誤類別
import eyed3                                      # eyed3 是一個用於處理 ID3 標籤的 Python 模組
from PIL import Image                             # PIL 是一個 Python 模組，用於處理圖像
import io                                         # io 模組提供了許多 I/O 相關的函數
import re                                         # re 模組提供了正則表達式的支持
import urllib                                     # urllib 模組提供了許多與網路相關的函數，用於剖析 URL
import logging                                    # logging 模組提供了 Python 的日誌功能
import tqdm                                       # tqdm 是一個 Python 模組，用於顯示進度條
import asyncio                                    # asyncio 是一個 Python 模組，用於支援非同步編程
import ssl                                        # ssl 模組提供了安全套接字層協議的支援
from functools import partial                     # functools 模組提供了一些高階函數
from eyed3.id3.frames import ImageFrame           # 引入 ImageFrame 類別，用於處理專輯封面
import pyperclip                                  # pyperclip 是一個 Python 模組，用於處理剪貼簿
import plyer.platforms.win.notification           # plyer 是一個 Python 模組，用於處理桌面通知
from plyer import notification                    # 引入 notification 類別，用於處理桌面通知
from functions.chkffmpeg import check_ffmpeg      # 引入 check_ffmpeg 函數，用於檢查 ffmpeg 是否存在
from pydub import AudioSegment                    # 引入 AudioSegment 類別，用於處理音頻文件

# 設定log
logging.basicConfig(
    level=logging.INFO,
    format='%(lineno)d: [%(asctime)s][%(levelname)s] - [%(module)s] %(message)s'
)
logging.getLogger('pytube').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('PIL').setLevel(logging.ERROR)
logging.getLogger('eyed3').setLevel(logging.ERROR)
logging.getLogger('pydub').setLevel(logging.ERROR)
logging.getLogger('plyer').setLevel(logging.ERROR)

logging.addLevelName(logging.DEBUG, "DEBG")
logging.addLevelName(logging.INFO, "INFO")
logging.addLevelName(logging.WARNING, "WARN")
logging.addLevelName(logging.ERROR, "ERRO")
logging.addLevelName(logging.CRITICAL, "CRIT")

"""
指令格式：

# 下載單一影片
python main.py download
    --single/-s "https://www.youtube.com/watch?v=xxxxxxxxxxx"     # 下載單一影片
    --output/-o "output"                                          # 輸出檔案路徑
    --noid3/-n                                                    # 不加入專輯封面、歌手等資訊
    --id3_latest/-i                                               # 使用最新的 id3 標籤格式

# 下載播放清單
python main.py download
    --playlist/-p "https://www.youtube.com/playlist?list=xxxxxxxxxxx"   # 下載播放清單
    --output/-o "output"                                                # 輸出資料夾
    --noid3/-n                                                          # 不加入專輯封面、歌手等資訊
    --id3_latest/-i                                                     # 使用最新的 id3 標籤格式
    --parallel_max/-m                                                   # 最大平行下載數
"""

ssl._create_default_https_context = ssl._create_stdlib_context

def progress_callback(pbar, stream, data_chunk, bytes_remaining):
    if pbar:
        pbar.update(len(data_chunk))

def sanitize_filename(filename):
    # 避免檔名中的特殊字元，換成底線
    logging.debug(f'檔名：{filename}')
    return re.sub(r'[\\/:*?"<>|]', '_', filename)

async def download_single(url, output, noid3, id3_latest):
    """
    Parameters
    ----------
    url : str
        影片網址
    output : str
        輸出檔案路徑
    noid3 : bool
        不加入專輯封面、歌手等資訊
    id3_latest : bool
        使用最新的 id3 標籤格式
    """
    # 下載影片
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        prbar = tqdm.tqdm(total=stream.filesize, unit="bytes")
        yt.register_on_progress_callback(partial(progress_callback, prbar))
        output_path = stream.download(output)
        prbar.close()
        logging.info(f'✅ 下載影片完成：{yt.title}')
    except urllib.error.URLError as e:                  # 網路錯誤
        logging.error(f'🟥 網路錯誤：{e}')
    except BotDetection as e:                           # 被偵測為機器人
        logging.error(f'🟥 被偵測為機器人，下載失敗。詳細錯誤訊息已輸出至 debug，如需檢視請在引數中加上 --debug 以查看！')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except VideoPrivate as e:                           # 影片為私人影片
        logging.error(f'🟥 影片為私人影片')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except MembersOnly as e:                            # 影片為會員限定
        logging.error(f'🟥 影片為會員限定')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except VideoRegionBlocked as e:                     # 影片在您的地區不可用
        logging.error(f'🟥 影片在您的地區不可用')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except LoginRequired as e:                          # 需要登入才能觀看此影片
        logging.error(f'🟥 需要登入才能觀看此影片')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except AgeRestrictedError as e:                          # 影片受年齡限制
        logging.error(f'🟥 影片受年齡限制')
        logging.debug(f'🟥 詳細錯誤訊息：{e}')
        return
    except VideoUnavailable as e:                       # 影片不存在
        logging.error(f'🟥 影片不存在：{e}')
        return
    except PytubeFixError as e:                         # PytubeFix 錯誤
        logging.error(f'🟥 下載失敗：{e}')
        return
    except Exception as e:                              # 其他錯誤
        logging.error(f'🟥 下載失敗：{e}')
        return
    
    # 將 m4a 轉換為 mp3
    sanitized_title = sanitize_filename(yt.title)
    mp3_filename = f'{sanitized_title}.mp3'
    mp3_output_path = os.path.join(output, mp3_filename)
    
    if output_path.endswith('.m4a'):
        logging.info(f'〰 轉換 m4a 檔案：{sanitized_title}.mp3')
        audio = AudioSegment.from_file(output_path, format="m4a")
        
        # 確保目錄存在
        mp3_output_dir = os.path.dirname(mp3_output_path)
        if not os.path.exists(mp3_output_dir):
            os.makedirs(mp3_output_dir)
        
        audio.export(mp3_output_path, format="mp3")
        os.remove(output_path)
        output_path = mp3_output_path
        logging.info(f'✅ 轉換 m4a 檔案完成：{sanitized_title}.mp3')

    # 加入專輯封面、歌手等資訊
    if noid3:
        return {"title": yt.title, "author": yt.author, "output": mp3_output_path}
    
    if id3_latest:
        ID3_VERSION = eyed3.id3.ID3_DEFAULT_VERSION
    else:
        ID3_VERSION = eyed3.id3.ID3_V2_3

    # 下載專輯封面
    if not os.path.exists('./temp'):
        os.makedirs('./temp')
    cover_url = yt.thumbnail_url
    cover_data = requests.get(cover_url).content
    cover = Image.open(io.BytesIO(cover_data))
    cover.save(f'./temp/cover-{yt.video_id}.jpg')
    
    # 加入專輯封面、歌手等資訊
    logging.info(f'💬 檔案路徑：{mp3_output_path}')
    audiofile = eyed3.load(mp3_output_path)
    if audiofile is None:
        logging.error(f'🟥 無法加載音頻文件：{mp3_output_path}')
        return
    audiofile.tag.artist = yt.author
    audiofile.tag.album = yt._title
    audiofile.tag.images.set(3, open(f'./temp/cover-{yt.video_id}.jpg', 'rb').read(), 'image/jpeg')
    audiofile.tag.save(
        version=ID3_VERSION,
        encoding='utf-8',
        preserve_file_time=True
    )
    os.remove(f'./temp/cover-{yt.video_id}.jpg')
    logging.info(f'✅ 加入專輯封面、歌手等資訊完成：{mp3_output_path}.mp3')

# 下載播放清單
async def download_video(url, output, noid3, id3_latest, semaphore):
    async with semaphore:
        await download_single(url, output, noid3, id3_latest)

# 定義指令群組
@click.group()
@click.option('--debug', '-d', is_flag=True, help='開啟除錯模式')
def cli(debug):
    ASCII_TEXT = rf"""
============================== YouTube Music Downloader ==============================

 _ _  ___  __ __           _        ___                   _              _           
| | ||_ _||  \  \ _ _  ___<_> ___  | . \ ___  _ _ _ ._ _ | | ___  ___  _| | ___  _ _ 
\   / | | |     || | |<_-<| |/ | ' | | |/ . \| | | || ' || |/ . \<_> |/ . |/ ._>| '_>
 |_|  |_| |_|_|_|`___|/__/|_|\_|_. |___/\___/|__/_/ |_|_||_|\___/<___|\___|\___.|_|  
                                                                                     

    Builder: SamHacker
    
    If you need command help, please type 'python main.py [command] --help'

============================== YouTube Music Downloader ==============================
    """
    for line in ASCII_TEXT.split('\n'):
        logging.info(line)

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('pytube').setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.DEBUG)
        logging.getLogger('PIL').setLevel(logging.DEBUG)
        logging.getLogger('eyed3').setLevel(logging.DEBUG)
        logging.getLogger('pydub').setLevel(logging.DEBUG)
        logging.getLogger('win10toast').setLevel(logging.DEBUG)
        logging.debug('⚠️ 開啟除錯模式')
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # 檢查 ffmpeg
    check_ffmpeg()

# 下載單一影片
@cli.command()
@click.option('--uri', '-l', help='單一影片網址', required=True)
@click.option('--output', '-o', help='輸出檔案路徑', default='./')
@click.option('--noid3', '-n', is_flag=True, help='不加入專輯封面、歌手等資訊')
@click.option('--id3_latest', '-i', is_flag=True, help='使用最新的 id3 標籤格式')
def single(uri, output, noid3, id3_latest):
    """
    下載單首歌曲

    \b
    參數：
    --uri, -l       目標影片網址，必填
    --output, -o         輸出資料夾，預設為當前目錄
    --noid3, -n          不加入專輯封面、歌手等資訊
    --id3_latest, -i     使用最新的 ID3 標籤格式
    """
    logging.info('💬 開始下載')
    single = uri
    # 檢查參數
    if not single:
        logging.error('🟥 未指定單一影片網址')
        return
    
    if id3_latest:
        logging.warning("⚠️ 注意：使用最新的 id3 標籤格式會造成部分播放器無法正確顯示專輯封面、歌手等資訊")
        logging.warning("⚠️ 目前已知 Windows 檔案總管、 Windows Media Player 及 Windows 內建的媒體撥放器（前稱 Grove 音樂）會無法正確顯示")
        logging.warning("⚠️ 建議使用 VLC、foobar2000、AIMP 等播放器，或移除此旗標以使用較舊的 id3 標籤格式（ID3 v2.3）")
    
    # 下載單一影片
    try:
        logging.info('💬 開始下載單一影片')
        asyncio.run(download_single(single, output, noid3, id3_latest))
    except Exception as e:
        logging.error(f'🟥 下載單一影片失敗：{e}')

# 下載播放清單
@cli.command()
@click.option('--uri', '-l', help='播放清單網址', required=True)
@click.option('--output', '-o', help='輸出資料夾', default='./')
@click.option('--noid3', '-n', is_flag=True, help='不加入專輯封面、歌手等資訊')
@click.option('--id3_latest', '-i', is_flag=True, help='使用最新的 id3 標籤格式')
@click.option('--parallel_max', '-m', help='最大平行下載數', default=5)
def list(uri, output, noid3, id3_latest, parallel_max):
    """
    批量下載播放清單

    \b
    參數：
    --uri, -l       播放清單網址，必填
    --output, -o         輸出資料夾，預設為當前目錄
    --noid3, -n          不加入專輯封面、歌手等資訊
    --id3_latest, -i     使用最新的 ID3 標籤格式
    --parallel_max, -m   最大平行下載數，預設為 5
    """
    logging.info('💬 開始下載')

    playlist = uri
    
    # 檢查參數
    if not playlist:
        logging.error('🟥 未指定播放清單網址')
        return
    
    if not output:
        logging.error('⚠️ 未指定輸出資料夾，將使用當前目錄')

    if id3_latest:
        logging.warning("⚠️ 注意：使用最新的 id3 標籤格式會造成部分播放器無法正確顯示專輯封面、歌手等資訊")
        logging.warning("⚠️ 目前已知 Windows 檔案總管、 Windows Media Player 及 Windows 內建的媒體撥放器（前稱 Grove 音樂）會無法正確顯示")
        logging.warning("⚠️ 建議使用 VLC、foobar2000、AIMP 等播放器，或移除此旗標以使用較舊的 id3 標籤格式（ID3 v2.3）")

    try:
        logging.info('💬 開始下載播放清單')
        playlist = Playlist(playlist)
        logging.info(f'💬 播放清單：{playlist.title}')
        logging.info(f'💬 影片數量：{len(playlist.videos)}')
        # output 設為當前目錄底下以播放清單名稱建立的資料夾
        output = f'./{output}/{playlist.title}'
        if not os.path.exists(output):
            os.makedirs(output)
        logging.info(f'💬 輸出資料夾：{output}')
        logging.info(f'💬 最大平行下載數：{parallel_max}')

        semaphore = asyncio.Semaphore(parallel_max)
        tasks = [download_video(video.watch_url, output, noid3, id3_latest, semaphore) for video in playlist.videos]

        async def run_tasks():
            await asyncio.gather(*tasks)
        asyncio.run(run_tasks())

        logging.info('✅ 下載播放清單完成')
    except Exception as e:
        logging.error(f'🟥 下載播放清單失敗：{e}')

# 啟動監聽模式
# 在監聽模式下，程式會持續監聽剪貼簿，當偵測到 YouTube 網址時，會自動下載影片
# 使用 re 模組判斷剪貼簿中的文字是否為 YouTube 網址
# 在偵測到並開始下載影片後，不將剪貼簿清空，並在桌面跳出通知
@cli.command()
@click.option('--no-notifaction', '-n', is_flag=True, help='關閉監聽模式的桌面通知')
def listen(no_notifaction):
    """
    啟動監聽模式，當偵測到 YouTube 網址時，自動下載影片

    \b
    參數：
    --no-notifaction, -n    關閉監聽模式的桌面通知
    """
    logging.info('✅ 開始監聽剪貼簿，如需退出此模式，執行 Ctrl + C 即可')
    notification.notify(
        title='YouTube Music Downloader',
        message='已啟動監聽模式，若要退出請回到終端視窗中按下 Ctrl + C 即可！',
        app_name='YouTube Music Downloader',
        timeout=10
    )
    # 先複製空白訊息，避免一開始剪貼簿中有 YouTube 網址
    pyperclip.copy('')
    try:
        while True:
            logging.debug('觸發定期監聽...')
            clipboard = pyperclip.paste()
            if re.match(r'https://www.youtube.com/watch\?v=.*', clipboard):
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'抓取到連結 {clipboard}\n開始下載影片',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                logging.info(f'✅ 偵測到 YouTube 網址：{clipboard}')
                asyncio.run(download_single(clipboard, './', False, False))
                # 桌面通知
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'影片下載完成',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                pyperclip.copy('')
            # 監聽是否為播放清單
            elif re.match(r'https://www.youtube.com/playlist\?list=.*', clipboard):
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'抓取到連結 {clipboard}\n開始下載影片',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                logging.info(f'✅ 偵測到 YouTube 播放清單：{clipboard}')
                asyncio.run(download_video(clipboard, './', False, False, 5))
                # 桌面通知
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'影片下載完成',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                pyperclip.copy('')
            # 監聽是否為 YouTube Music 影片網址，如果是就將前方的 music 去除
            elif re.match(r'https://music.youtube.com/watch\?v=.*', clipboard):
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'抓取到連結 {clipboard}\n開始下載影片',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                logging.info(f'✅ 偵測到 YouTube Music 網址：{clipboard}')
                clipboard = clipboard.replace('music.', '')
                asyncio.run(download_single(clipboard, './', False, False))
                # 桌面通知
                if not no_notifaction:
                    notification.notify(
                        title='YouTube Music Downloader',
                        message=f'影片下載完成',
                        app_name='YouTube Music Downloader',
                        timeout=10
                    )
                pyperclip.copy('')
            time.sleep(0.5)
    except KeyboardInterrupt:
        logging.info('✅ 退出監聽模式，掰掰！')
        sys.exit(0)
    except Exception as e:
        logging.error(f'🟥 監聽模式發生錯誤，詳細情形請啟動除錯模式')
        logging.debug(f'🟥 錯誤訊息：{e}')
        sys.exit(1)

if __name__ == '__main__':
    cli()