# YouTUbe音樂下載器，使用pytube、與click，並透過eyed3加入專輯封面
# 作者：SamHacker

import click
import os
import sys
import time
import requests
from pytubefix import YouTube, Playlist, Stream
from pytubefix.cli import on_progress
from pytubefix.exceptions import PytubeFixError
from pytubefix.exceptions import VideoUnavailable
import eyed3
from PIL import Image
import io
import re
import urllib
import logging
import tqdm
import asyncio
import ssl
from functools import partial
from eyed3.id3.frames import ImageFrame
from pydub import AudioSegment
import pyperclip
from win10toast import ToastNotifier

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
logging.getLogger('win10toast').setLevel(logging.ERROR)

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
    # try:
    yt = YouTube(url)
    stream = yt.streams.filter(only_audio=True).first()
    prbar = tqdm.tqdm(total=stream.filesize, unit="bytes")
    logging.info(f'download_single中的prbar：{prbar}')
    yt.register_on_progress_callback(partial(progress_callback, prbar))
    output_path = stream.download(output)
    prbar.close()
    logging.info(f'下載影片完成：{yt.title}')
    # except VideoUnavailable as e:
    #     logging.error(f'影片不存在：{e}')
    #     return
    # except PytubeFixError as e:
    #     logging.error(f'下載失敗：{e}')
    #     return
    # except Exception as e:
    #     logging.error(f'下載失敗：{e}')
    #     return
    
    # 將 m4a 轉換為 mp3
    sanitized_title = sanitize_filename(yt.title)
    mp3_filename = f'{sanitized_title}.mp3'
    mp3_output_path = os.path.join(output, mp3_filename)
    
    if output_path.endswith('.m4a'):
        logging.info(f'轉換 m4a 檔案：{sanitized_title}.mp3')
        audio = AudioSegment.from_file(output_path, format="m4a")
        
        # 確保目錄存在
        mp3_output_dir = os.path.dirname(mp3_output_path)
        if not os.path.exists(mp3_output_dir):
            os.makedirs(mp3_output_dir)
        
        audio.export(mp3_output_path, format="mp3")
        os.remove(output_path)
        output_path = mp3_output_path
        logging.info(f'轉換 m4a 檔案完成：{sanitized_title}.mp3')

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
    logging.info(f'檔案路徑：{mp3_output_path}')
    audiofile = eyed3.load(mp3_output_path)
    if audiofile is None:
        logging.error(f'無法加載音頻文件：{mp3_output_path}')
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
    logging.info(f'加入專輯封面、歌手等資訊完成：{mp3_output_path}.mp3')

# 下載播放清單
async def download_video(url, output, noid3, id3_latest, semaphore):
    async with semaphore:
        await download_single(url, output, noid3, id3_latest)

# 定義指令群組
@click.group()
@click.option('--debug', '-d', is_flag=True, help='開啟除錯模式')
def cli(debug):
    # 檢查是否有 ffmpeg
    # if not os.path.exists('ffmpeg.exe') or not os.path.exists('ffmpeg'):
    #     logging.error('找不到 ffmpeg.exe，請確認是否已安裝 ffmpeg')
    #     sys.exit(1)
    # else:
    #     logging.info('找到 ffmpeg.exe')
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
        logging.debug('開啟除錯模式')
    else:
        logging.getLogger().setLevel(logging.INFO)

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
    logging.info('開始下載')
    single = uri
    # 檢查參數
    if not single:
        logging.error('未指定單一影片網址')
        return
    
    if id3_latest:
        logging.warning("注意：使用最新的 id3 標籤格式會造成部分播放器無法正確顯示專輯封面、歌手等資訊")
        logging.warning("目前已知 Windows 檔案總管、 Windows Media Player 及 Windows 內建的媒體撥放器（前稱 Grove 音樂）會無法正確顯示")
        logging.warning("建議使用 VLC、foobar2000、AIMP 等播放器，或移除此旗標以使用較舊的 id3 標籤格式（ID3 v2.3）")
    
    # 下載單一影片
    try:
        logging.info('開始下載單一影片')
        asyncio.run(download_single(single, output, noid3, id3_latest))
    except Exception as e:
        logging.error(f'下載單一影片失敗：{e}')

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
    logging.info('開始下載')

    playlist = uri
    
    # 檢查參數
    if not playlist:
        logging.error('未指定播放清單網址')
        return
    
    if not output:
        logging.error('未指定輸出資料夾，將使用當前目錄')

    if id3_latest:
        logging.warning("注意：使用最新的 id3 標籤格式會造成部分播放器無法正確顯示專輯封面、歌手等資訊")
        logging.warning("目前已知 Windows 檔案總管、 Windows Media Player 及 Windows 內建的媒體撥放器（前稱 Grove 音樂）會無法正確顯示")
        logging.warning("建議使用 VLC、foobar2000、AIMP 等播放器，或移除此旗標以使用較舊的 id3 標籤格式（ID3 v2.3）")

    try:
        logging.info('開始下載播放清單')
        playlist = Playlist(playlist)
        logging.info(f'播放清單：{playlist.title}')
        logging.info(f'影片數量：{len(playlist.videos)}')
        # output 設為當前目錄底下以播放清單名稱建立的資料夾
        output = f'./{output}/{playlist.title}'
        if not os.path.exists(output):
            os.makedirs(output)
        logging.info(f'輸出資料夾：{output}')
        logging.info(f'最大平行下載數：{parallel_max}')

        semaphore = asyncio.Semaphore(parallel_max)
        tasks = [download_video(video.watch_url, output, noid3, id3_latest, semaphore) for video in playlist.videos]

        async def run_tasks():
            await asyncio.gather(*tasks)
        asyncio.run(run_tasks())

        logging.info('下載播放清單完成')
    except Exception as e:
        logging.error(f'下載播放清單失敗：{e}')

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
    logging.info('開始監聽剪貼簿，如需退出此模式，執行 Ctrl + C 即可')
    tn = ToastNotifier()
    tn.show_toast('YouTube Music Downloader', '已啟動監聽模式，\n若要退出請回到終端視窗中按下 Ctrl + C 即可！', duration=10)
    try:
        while True:
            logging.debug('觸發定期監聽...')
            clipboard = pyperclip.paste()
            if re.match(r'https://www.youtube.com/watch\?v=.*', clipboard):
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n開始下載影片', duration=10)
                logging.info(f'偵測到 YouTube 網址：{clipboard}')
                asyncio.run(download_single(clipboard, './', False, False))
                # 桌面通知
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n影片下載完成', duration=10)
                # pyperclip.copy('')
            # 監聽是否為播放清單
            elif re.match(r'https://www.youtube.com/playlist\?list=.*', clipboard):
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n開始下載播放清單', duration=10)
                logging.info(f'偵測到 YouTube 播放清單：{clipboard}')
                asyncio.run(download_video(clipboard, './', False, False, 5))
                # 桌面通知
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n播放清單下載完成', duration=10)
                # pyperclip.copy('')
            # 監聽是否為 YouTube Music 影片網址，如果是就將前方的 music 去除
            elif re.match(r'https://music.youtube.com/watch\?v=.*', clipboard):
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n開始下載影片', duration=10)
                logging.info(f'偵測到 YouTube Music 網址：{clipboard}')
                clipboard = clipboard.replace('music.', '')
                asyncio.run(download_single(clipboard, './', False, False))
                # 桌面通知
                if not no_notifaction:
                    tn.show_toast('YouTube Music Downloader', f'抓取到連結 {clipboard}\n影片下載完成', duration=10)
                # pyperclip.copy('')
            time.sleep(0.5)
    except KeyboardInterrupt:
        logging.info('退出監聽模式，掰掰！')
        return

if __name__ == '__main__':
    cli()