import cv2

import configparser
import math
import tkinter
from tkinter import filedialog, messagebox
import os
import sys

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

counter = 1
prevX = 0
prevY = 0

if config["SETTINGS"]["UseSelectWindow"].upper() == "TRUE":
    root = tkinter.Tk()
    root.withdraw()
    filetypes = [("すべてのファイル", "*.*")]
    filePath = tkinter.filedialog.askopenfilename(filetypes=filetypes, initialdir=os.path.abspath(os.path.dirname(__file__)))
    
    if not len(filePath):
        print("[Error] ファイルが選択されていません。Configで指定されたファイルを読み込みます")
        filePath = str(config['SETTINGS']['Path'])

else:
    filePath = str(config['SETTINGS']['Path'])

print(f"読み込むファイル名: {filePath}")

def onMouse(event, x, y, flags, params):
    global prevX, prevY, counter
    
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"#{counter} Pos: ({x}, {y}) / Diff: {y - prevY} ({x - prevX}, {y - prevY})")
        prevX = x
        prevY = y
        counter += 1

try:
    frame = cv2.imread(filePath)
    frame = cv2.resize(frame, (int(config["SETTINGS"]["ScreenX"]), int(config["SETTINGS"]["ScreenY"])))

except:
    tkinter.messagebox.showerror("エラー", "ファイルが読み込めません")
    sys.exit(0)

else:
    print("Escキーで処理を終了します")

cv2.imshow("Micrometer", frame)

while True:
    cv2.setMouseCallback('Micrometer', onMouse)
    
    # qキーの押下で処理を中止
    key = cv2.waitKey(1) & 0xFF
    if key == 27: break #escで消える

#メモリの解放
cv2.destroyAllWindows()
