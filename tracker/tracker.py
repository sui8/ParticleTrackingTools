import cv2
import numpy as np

import configparser
import tkinter as tk
import tkinter.filedialog
from decimal import Decimal, ROUND_HALF_UP
from math import log10, floor
import os
import sys

config = configparser.ConfigParser()
config.read('config.ini', encoding = 'utf-8')


''' 関数定義 '''

# Tracker初期化
def initTracker(windowName, frame):
    '''
    Trackerを初期化する。
    '''

    # DaSiamRPN
    params = cv2.TrackerDaSiamRPN_Params()
    params.model = "model/dasiamrpn_model.onnx"
    params.kernel_r1 = "model/dasiamrpn_kernel_r1.onnx"
    params.kernel_cls1 = "model/dasiamrpn_kernel_cls1.onnx"
    tracker = cv2.TrackerDaSiamRPN_create(params)
            

    # 関心領域指定
    while True:
        print("追跡範囲を指定してください")
        print("EnterまたはSpaceキーを押下して追跡を開始します")
        print("Escキーで終了します")
        target = cv2.selectROI(windowName, frame, showCrosshair=False)

        try:
            tracker.init(frame, target)

        except Exception as e:
            print(e)
            continue

        return tracker
    

def calc_dig(num):
    '''
    数字の桁数を計算する。
    
    Parameters
    ----------
    num : int or float
        桁数を算出する数値
    
    Returns
    -------
    digits : int
        算出した桁数
    '''
    
    if num == 0:
        digits = 1
    else:
        digits = int(floor(log10(abs(num)))) + 1  #桁数算出
    return digits


def decimalRound(num, sig): 
    '''
    decimalを用いて四捨五入する。

    Parameters
    ----------
    num : int or float
        四捨五入する数値

    Returns
    -------
    roundedNum : int or float
        四捨五入された数値
    '''
    
    num = Decimal(str(num))  
    dig = "1E" + str(calc_dig(num) - sig)  # 四捨五入する位を求める(1E1なら1の位で四捨五入)
    roundedNum = num.quantize(Decimal(dig), rounding = ROUND_HALF_UP)
    
    if "E" in str(roundedNum):
        return int(roundedNum)  # 整数の場合にEで表示されることを回避
    
    else:
        return float(roundedNum)


def calc_center(coodinates): 
    '''
    粒子の中心座標(x, y)を求める。
    引数は整数値にする必要あり。 

    Parameters
    ----------
    coordinates : list of int
        それぞれx左端(0), y上端(1), width(2), height(3)の値を格納したリスト。

    Returns
    -------
    x_center : int
        粒子中心のx座標
    y_center : int
        粒子中心のy座標
    '''
    
    x_center = coodinates[0] + (coodinates[2] - 1) / 2
    x_center = int(decimalRound(x_center, calc_dig(x_center)))
    y_center = coodinates[1] + (coodinates[3] - 1) / 2
    y_center = int(decimalRound(y_center, calc_dig(y_center)))
    return x_center, y_center


# 移動距離の測定
def measure(x_list, y_list, ptlMileageSum, px):
    '''
    移動距離の測定

    Parameters
    ----------
    x_list : list of int
        各フレームにおける粒子位置のx座標
    y_list : list of int
        各フレームにおける粒子位置のy座標
    ptlMillageSum : int or float
        粒子の総移動距離(単位: ピクセル)
    px : int
        ミクロメーター1目盛り(10μm)あたりのピクセル数
    '''
    
    # 1ピクセルが何μmに当たるか定義
    scale_per_pxl = decimalRound(10 / px, len(str(px)))

    x = max(x_list) - min(x_list) 
    y = max(y_list) - min(y_list)
    width = decimalRound(x * scale_per_pxl, min(calc_dig(x), calc_dig(px))) 
    height = decimalRound(y * scale_per_pxl, min(calc_dig(y), calc_dig(px)))
    ptlMileageSum = decimalRound(ptlMileageSum * scale_per_pxl, 
                                 min(calc_dig(ptlMileageSum), calc_dig(px)))
    strait = np.round(np.linalg.norm(np.array([x_list[0], y_list[0]]) - np.array([x_list[-1], y_list[-1]])), 3)
    ptlMileageStrait = decimalRound(strait * scale_per_pxl, min(calc_dig(strait), calc_dig(px)))

    print(f"移動距離: {ptlMileageSum}")
    print(f"直線距離: {ptlMileageStrait}")
    print(f"横幅: {width}")
    print(f"縦幅: {height}")
    
''' '''


# 単位変換 (1目盛り10μm)
pxl = int(config['SETTINGS']['Pixel'])
windowName = "Tracker"
sum_dist = 0
x_list = []
y_list = []

# 動画ファイル準備
if str(config['PATH']['UseSelectWindow']).upper() == "TRUE":
    root = tk.Tk()
    root.withdraw()
    filetypes = [("MP4 ファイル", "*.mp4"), ("すべてのファイル", "*.*")]
    videoPath = tkinter.filedialog.askopenfilename(filetypes=filetypes, initialdir=os.path.abspath(os.path.dirname(__file__)))
    
    if not len(videoPath):
        print("[Error] ファイルが選択されていません。Configで指定されたファイルを読み込みます")
        videoPath = str(config['PATH']['Video'])

else:
    videoPath = str(config['PATH']['Video'])

# カメラ準備
cap = cv2.VideoCapture(videoPath)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 540)


# Tracker初期化
cv2.namedWindow(windowName)

isFrameLoaded, frame = cap.read()

if not isFrameLoaded:
    print("[Error] 動画の読み込みに失敗しました")
    exit()

else:
    print(f"{videoPath} を読み込みました")

tracker = initTracker(windowName, frame)

trackingTime = float(input("> 追跡する秒数を入力してください: "))
trackingTime = floor(trackingTime * 10) / 10 
fps = int(cap.get(cv2.CAP_PROP_FPS))

if trackingTime.is_integer():
    trackingTime = int(trackingTime)
    ts = trackingTime
    tms = 0

else:
    ts, tms = str(trackingTime).split(".")

# 30, 60 FPS時は追跡秒数を小数第一位まで受け入れる
if fps == 60:
    print("FPS: 60")
    endFlameNum = (fps * int(ts)) + (6 * int(tms)) # 追跡終了時のフレーム番号 (

elif fps == 30:
    print("FPS: 30")
    endFlameNum = (fps * int(ts)) + (3 * int(tms)) # 追跡終了時のフレーム番号

else:
    print("FPSが30または60ではありません。追跡秒数の小数点以下を無視します")
    endFlameNum = (fps * int(ts)) # 追跡終了時のフレーム番号
                                     
flameNum = 0


# 稼働開始
while cap.isOpened():
    isFrameLoaded, frame = cap.read()
    flameNum += 1

    if not isFrameLoaded:
        print("追跡が終了しました")
        print(f"現在の経過時間{decimalRound(num = flameNum / fps, sig = len(str(flameNum)))}[秒]") 
        measure(x_list, y_list, sum_dist, pxl) # 移動距離計算

        break

    frame_prev = frame.copy()

    # 追跡アップデート
    isOK, target = tracker.update(frame)
    
    if isOK:
        # 追跡後のボックス描画
        box = []
        box.append(int(target[0]))
        box.append(int(target[1]))
        box.append(int(target[2]))
        box.append(int(target[3]))
        cv2.rectangle(frame_prev, box, [0, 0, 255], thickness=1)

        track_x, track_y = calc_center(box)

        if len(x_list) < 1:
            x_list.append(track_x)
            y_list.append(track_y)
            
        # 移動距離をsum_distに加算
        sum_dist += np.round(np.linalg.norm(np.array([x_list[-1], y_list[-1]]) - np.array([track_x, track_y])), 2)
                
        # 粒子の現在地をリストに追加
        x_list.append(track_x)
        y_list.append(track_y)
        cv2.drawMarker(frame, (track_x, track_y), (255, 0, 255), markerSize=5)

        
        # 軌跡の点を直線で結ぶ
        for i in range(1, len(x_list)):
            cv2.line(frame_prev, (x_list[i-1], y_list[i-1]), (x_list[i], y_list[i]), (255, 0, 0))

        
    cv2.imshow(windowName, frame_prev)

    key = cv2.waitKey(1)
    
    if key == 32:  # SPACE
        # 追跡対象再指定
        tracker = initTracker(windowName, frame)
        
    #Escで終了
    if key == 27:
        print(f"現在の経過時間{decimalRound(num = flameNum / fps, sig = len(str(flameNum)))}[秒]") 
        measure(x_list, y_list, sum_dist, pxl) # 移動距離計算
        break

    if flameNum == endFlameNum:
        print(f"{trackingTime}秒間追跡が終了しました")
        measure(x_list, y_list, sum_dist, pxl) # 移動距離計算
        break
    

cv2.destroyAllWindows()
print("追跡を終了しました。")
os.system("PAUSE")
sys.exit()
