import cv2
from IPython.display import Image, display

import tkinter
from tkinter import filedialog, messagebox
import math
import os

## マウス処理
def onMouse(event, x, y, flag, params):
    raw_img = params["img"]
    wname = params["wname"]
    point_list = params["point_list"]
    point_num = params["point_num"]
    
    ## クリックイベント
    ### 左クリックでポイント追加
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(point_list) < point_num:
            point_list.append([x, y])
    
    ### 右クリックでポイント削除
    if event == cv2.EVENT_RBUTTONDOWN:
        if len(point_list) > 0:
            point_list.pop(-1)

    ## レーダーの作成, 描画
    img = raw_img.copy()
    h, w = img.shape[0], img.shape[1]
    cv2.line(img, (x, 0), (x, h), (255, 0, 0), 1)
    cv2.line(img, (0, y), (w, y), (255, 0, 0), 1)

    ## 点, 線の描画
    for i in range(len(point_list)):
        cv2.circle(img, (point_list[i][0], point_list[i][1]), 3, (0, 0, 255), 3)
        if 0 < i:
            cv2.line(img, (point_list[i][0], point_list[i][1]),
                     (point_list[i-1][0], point_list[i-1][1]), (0, 255, 0), 2)
        if i == point_num-1:
            cv2.line(img, (point_list[i][0], point_list[i][1]),
                     (point_list[0][0], point_list[0][1]), (0, 255, 0), 2)
    
    if 0 < len(point_list) < point_num:
        cv2.line(img, (x, y),
                     (point_list[len(point_list)-1][0], point_list[len(point_list)-1][1]), (0, 255, 0), 2)

    cv2.putText(img, "({0}, {1})".format(x, y), (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imshow(wname, img)
    

#回転角度を求める
def calc_rotation_angle(left_pos, right_pos):
    x = right_pos[0] - left_pos[0]
    y = right_pos[1] - left_pos[1]
    return math.degrees(math.atan2(y, x))

#openCVをウィンドウ上で出力
def imshow(img):
    ret, encoded = cv2.imencode(".jpg", img)
    display(Image(encoded))

#回転の座標指定
def rotate_img(img, angle):
    size = tuple([img.shape[1], img.shape[0]])
    center = tuple([size[0] // 2, size[1] // 2])
    mat = cv2.getRotationMatrix2D(center, angle, scale=1.0)
    rot_img = cv2.warpAffine(img, mat, size, flags=cv2.INTER_CUBIC)
    return rot_img

def main():
    root= tkinter.Tk()
    root.attributes("-topmost", True)
    file_path = filedialog.askopenfilename()
    root.withdraw()
    img = cv2.imread(file_path)

    wname = "MouseEvent"
    point_list = []
    point_num = 2
    params = {
        "img": img,
        "wname": wname,
        "point_list": point_list,
        "point_num": point_num,
    }

    ## メイン
    cv2.namedWindow(wname)
    cv2.setMouseCallback(wname, onMouse, params)

    try:
        cv2.imshow(wname, img)

    except:
        tkinter.messagebox.showerror("エラー", "ファイルが読み込めません")
        sys.exit(0)
        
    cv2.moveWindow(wname, 10, 20)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    angle = calc_rotation_angle(point_list[0], point_list[1])
    if (angle<=-90):
        angle+=180

    angle += 270
    
    #ベースネームを取得
    name = os.path.basename(file_path)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

    root = tkinter.Tk()
    root.withdraw()
    folder = tkinter.filedialog.askdirectory(title="保存先を指定", initialdir=parent_dir)
    
    if not len(folder):
        savePath = os.path.join(parent_dir, f"rot_{name}")

    else:
        savePath = os.path.join(folder, f"rot_{name}")
    
    rot_img = rotate_img(img,angle)
    
    cv2.imwrite(savePath , rot_img)
    print(f"ファイルを次の場所に保存しました: {savePath}")

if __name__ == "__main__":
    main()

