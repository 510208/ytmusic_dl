# Original Code is builded by pydub utils.py (which: Line 144, )
# The following code is copied from pydub's utils.py
# pydub is licensed under the MIT License
# 
# Copyright (C) 2025 SamHacker (samhacker.xyz)
# 本檔案屬於 GNU General Public License v3.0 開源專案的一部分。
# 
# 根據 MIT 授權條款，以下內容來自 pydub：
# 
# MIT License
# 
# Copyright (c) 2011 James Robert, http://jiaaro.com

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---
# 
# 此檔案屬於 GPL v3.0 授權的專案，並整合了來自 pydub 的部分程式碼
# 根據 GPL v3.0，整個專案必須遵循 GPL v3.0 的開源條款。
# 若使用本專案，您必須遵守 GPL v3.0 授權規範。
#
# 本專案授權條款請參閱 LICENSE 文件。

import os
import logging

logger = logging.getLogger(__name__)

def which(program):
    """
    Mimics behavior of UNIX which command.
    """
    # Add .exe program extension for windows support
    if os.name == "nt" and not program.endswith(".exe"):
        program += ".exe"

    envdir_list = [os.curdir] + os.environ["PATH"].split(os.pathsep)

    for envdir in envdir_list:
        program_path = os.path.join(envdir, program)
        if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
            return program_path
        
    return None

def check_ffmpeg():
    """
    Return enconder default application for system, either avconv or ffmpeg
    """
    if which("avconv") or which("ffmpeg"):
        logger.debug("✅ 成功找到 FFmpeg！")
        return True
    else:
        # should raise exception
        MESSAGE = """
⚠️⚠️⚠ 找不到 FFmpeg！ ⚠️⚠️⚠️

本程式在你的電腦中搜尋 FFmpeg（或 avconv），但沒有找到適合的版本。  
如果你還沒安裝 FFmpeg，請到官方網站下載預編譯版本，並依照 README.md 的指示，  
將它放入本軟體可讀取的路徑中。  

如果這是已編譯好的版本，請檢查同目錄下是否有 `ffmpeg`。  
如果沒有，請回報 Issue，可能是我忘了放進去 😅。
"""
#         MESSAGE_ENG = """
# ⚠️⚠️⚠️ FFmpeg not found! ⚠️⚠️⚠️

# This program tried to find FFmpeg (or avconv) on your computer, but no compatible version was found.  
# If you haven’t installed FFmpeg yet, please download a prebuilt version from the official website  
# and follow the instructions in `README.md` to place it in a readable path.  

# If this is a precompiled version, check if `ffmpeg` exists in the same directory.  
# If not, please open an issue—I might have forgotten to include it 😅.
# """
        # 逐行輸出
        for line in MESSAGE.split("\n"):
            logger.error(line)
        # logger.warning(MESSAGE_ENG)
        return False