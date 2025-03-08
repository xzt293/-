import cv2
import time
import threading
import re
import matplotlib.pyplot as plt
import argparse
import math
import gc
import numpy as np

# esp32
import socket
import io
from PIL import Image

# yolo
from ultralytics.yolo.v8.detect import DetectionPredictor

# mediapipe
import cv2
import mediapipe as mp
# 手：19 20
# 嘴：9 10
#对应：9靠近19，10靠近20


# ui
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from eat_ui import Ui_Form


img_path_down = "/home/lilili/eat/yolov8/run_img/img_down.jpg"
img_path_up = "/home/lilili/eat/yolov8/run_img/img_up.jpg"

'''
# USB摄像头
while True:
  video_down = cv2.VideoCapture('/dev/video4')           # 定义摄像头对象
  if video_down.isOpened() is True:
    print('摄像头已打开。')
    # self.video_down.release()
    video_down.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_down.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    break
  elif video_down.isOpened() is False:
    print('未接入摄像头。')

while True:
  video_up = cv2.VideoCapture('/dev/video0')           # 定义摄像头对象
  if video_up.isOpened() is True:
    print('摄像头已打开。')
    # self.video_up.release()
    video_up.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_up.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    break
  elif video_up.isOpened() is False:
    print('未接入摄像头。')
'''

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)     # 创建套接字
s.bind(("0.0.0.0", 9090))   # 监听所有可用IP地址

img_up = np.zeros((640, 480, 3), np.uint8)
img_down = np.zeros((640, 480, 3), np.uint8)
img_up.fill(255)
img_down.fill(255)

class workThread(QThread):      # 读取图像
    finishSignal = pyqtSignal(str)

    # 带一个参数t
    def __init__(self, parent=None):
        super(workThread, self).__init__(parent)

    #run函数是子线程中的操作，线程启动后开始执行
    def run(self):
      global img_up     # 摄像头1图像
      global img_down   # 摄像头2图像
      while True:
        data, IP = s.recvfrom(100000)
        # print(data)
        # print(IP)
        if IP[0] == '10.42.0.123':
            # print("前置摄像头已开启.")
            bytes_stream = io.BytesIO(data)     # 读取data
            image1 = Image.open(bytes_stream)
            img_up = np.asarray(image1)         # 转换为numpy数组
            img_up = cv2.cvtColor(img_up, cv2.COLOR_RGB2BGR)  # ESP32采集的是RGB格式，要转换为BGR（opencv的格式）
            cv2.flip(img_up, 1, img_up)

            '''
            # 摄像头1测试
            cv2.imshow("camera1", img1)
            if cv2.waitKey(1) == ord("a"):
                img1_name = "img1/%d.jpg" % img1_num
                img1_num += 1
                print(img1_name)
                cv2.imwrite(img1_name, img1)
            '''

        if IP[0] == '10.42.0.189':
            # print("桌面摄像头已开启.")
            bytes_stream = io.BytesIO(data)
            image2 = Image.open(bytes_stream)
            img_down = np.asarray(image2)
            img_down = cv2.cvtColor(img_down, cv2.COLOR_RGB2BGR)  # ESP32采集的是RGB格式，要转换为BGR（opencv的格式）
            cv2.flip(img_down, 0, img_down)
            cv2.flip(img_down, 1, img_down)

            '''
            # 摄像头2测试
            cv2.imshow("camera2", img2)
            if cv2.waitKey(1) == ord("a"):
                img2_name = "img2/%d.jpg" % img2_num
                img2_num += 1
                print(img2_name)
                cv2.imwrite(img2_name, img2)
            '''

        '''
        ret_up, img_up = video_up.read()
        ret_down, img_down = video_down.read()
        if ret_down:
          img_down = cv2.resize(img_down, (640, 480))
          #cv2.imwrite(img_path_down, img_down)
        if ret_up:
          img_up = cv2.resize(img_up, (640, 480))
          #cv2.imwrite(img_path_up, img_up)
        time.sleep(0.03)
        '''

        #i = 1        
        #self.finishSignal.emit(str(i))  # 注意这里与_signal = pyqtSignal(str)中的类型相同


# widget
class MyWidget(Ui_Form, QWidget):
    def __init__(self):
        super(MyWidget, self).__init__()
        self.setupUi(self)

        self.model_path = "/home/lilili/eat/yolov8/model/eat9.pt"

        self.now_edit.setStyleSheet("color:red")        # 设置label字体颜色

        # 按键初始化
        self.start_Button_eat.setCheckable(True)
        self.start_Button_eat.clicked.connect(self.start_eat_def)
        self.close_Button_eat.setCheckable(True)
        self.close_Button_eat.clicked.connect(self.close_eat_def)

        self.start_Button_pose.setCheckable(True)
        self.start_Button_pose.clicked.connect(self.start_pose_def)
        self.close_Button_pose.setCheckable(True)
        self.close_Button_pose.clicked.connect(self.close_pose_def)

        self.start_Button_danger.setCheckable(True)
        self.start_Button_danger.clicked.connect(self.start_danger_def)
        self.close_Button_danger.setCheckable(True)
        self.close_Button_danger.clicked.connect(self.close_danger_def)

        self.write_img_name = 42
        self.img_l = 'img_new/%d.jpg' % self.write_img_name
        self.get_img_button.setCheckable(True)
        self.get_img_button.clicked.connect(self.get_img_def)


        self.test_Button.setCheckable(True)
        self.test_Button.clicked.connect(self.test_def)

        self.print_Button.setCheckable(True)
        self.print_Button.clicked.connect(self.print_def)

        self.print_Button.setCheckable(True)
        self.print_Button.clicked.connect(self.print_def)

        self.s1_return_button.setCheckable(True)
        self.s1_return_button.clicked.connect(self.s1_re_def)
        self.s2_return_button.setCheckable(True)
        self.s2_return_button.clicked.connect(self.s2_re_def)
        self.s1_add1_button.setCheckable(True)
        self.s1_add1_button.clicked.connect(self.s1_add1_def)
        self.s1_add10_button.setCheckable(True)
        self.s1_add10_button.clicked.connect(self.s1_add10_def)
        self.s1_sub1_button.setCheckable(True)
        self.s1_sub1_button.clicked.connect(self.s1_sub1_def)
        self.s1_sub10_button.setCheckable(True)
        self.s1_sub10_button.clicked.connect(self.s1_sub10_def)
        self.s2_add1_button.setCheckable(True)
        self.s2_add1_button.clicked.connect(self.s2_add1_def)
        self.s2_add10_button.setCheckable(True)
        self.s2_add10_button.clicked.connect(self.s2_add10_def)
        self.s2_sub1_button.setCheckable(True)
        self.s2_sub1_button.clicked.connect(self.s2_sub1_def)
        self.s2_sub10_button.setCheckable(True)
        self.s2_sub10_button.clicked.connect(self.s2_sub10_def)


        self.model_ch_Button.setCheckable(True)
        self.model_ch_Button.clicked.connect(self.model_ch_def)

        self.l_x = 0
        self.l_y = 0
        self.low_xy = 0
        self.now_xy = 0
        self.low_num = 0
        self.t_x = 320
        self.t_y = 240

        self.s1_num = 77
        self.s2_num = 77
        self.s1_print = 's1%03d' % self.s1_num
        self.s2_print = 's2%03d' % self.s2_num

        self.test_on_off = 0
        self.yolo_on_off = 0
        self.eat_on_off = 0
        self.pose_on_off = 0
        self.danger_on_off = 0

        self.now_model_label.setText("家长模式")
        self.model_ch = 0

        self.person_run = 0

        self.find_eat = 0
        self.previous_eat_number = 0
        self.eat_disappear = 0
        self.pose_to_eat = 0

        self.ptLeftTop = (0, 0)           # 左上角坐标
        self.ptRightBottom = (10, 10)     # 右下角坐标

        self.face_color = (255, 0, 0)     # 人类颜色
        self.person_color = (0, 255, 0)   # 脸类颜色
        self.pill_color = (0, 0, 255)   # 脸类颜色
        self.coin_color = (255, 0, 255)   # 硬币类颜色
        self.knife_color = (255, 255, 0)   # 水果刀/菜刀类颜色
        self.clipper_color = (0, 255, 255)   # 剪刀类颜色

        self.thickness = 3                # 线宽度
        self.lineType = 4                 # 线类型

        self.person_number = 0            # 镜头内人数
        self.pill_number = 0              # 镜头内药品数
        self.coin_number = 0              # 镜头内硬币数
        self.eat_number = 0               # 镜头内易误食物品数
        self.knife_number = 0             # 镜头内水果刀/菜刀数
        self.clipper_number = 0           # 镜头内剪刀数
        self.danger_number = 0            # 镜头内危险物品数
        self.long_eat_number = 0          # 镜头内存在一段时间的易误食物品数
        self.long_num = 0                 # 计数

        # 初始化
        self.eat_class_label.setText("药物:%d个\n硬币:%d个\n" % (self.pill_number, self.coin_number))
        self.danger_class_label.setText("水果刀/菜刀:%d个\n剪刀:%d个\n" % (self.knife_number, self.clipper_number))

        # yolo使用列表
        self.boxes = []
        self.box = []

        # yolo配置
        self.args_yolo = dict(model=self.model_path, source=img_path_down, name="eat_export", save=True)
        self.args_person = dict(model=self.model_path, source=img_path_up, name="eat_export", save=True)
        # save_txt=True, show=True

        # mediapipe配置
        self.mp_drawing = mp.solutions.drawing_utils     # 绘制工具

        #参数：(颜色, 线条粗细, 点的半径)
        self.DrawingSpec_point = self.mp_drawing.DrawingSpec((0, 255, 0), 2, 2)
        self.DrawingSpec_line = self.mp_drawing.DrawingSpec((0, 0, 255), 2, 2)
         
        # 模型定义
        self.mp_pose = mp.solutions.pose
        # mp.solutions.holistic: 人整体
        self.pose_model = self.mp_pose.Pose(static_image_mode=True)
            
        self.timer = QTimer(self)                 # 定义主定时器
        self.timer_yolov8 = QTimer(self)          # 定义yolo运行定时器
        self.timer_mediapipe = QTimer(self)       # 定义mediapipe运行定时器
        self.timer_test = QTimer(self)            # 定义test运行定时器
        self.low_timer = QTimer(self)             # 定义下位机信号发送的定时器
        self.thread = workThread()
        self.thread.start()
        self.timer_init()

    def start_eat_def(self):
        self.eat_on_off = 1
        if self.yolo_on_off == 0:
          self.timer_yolov8.start(250)
          self.timer_yolov8.timeout.connect(self.yolov8_run)
          self.yolo_on_off = 1
        else:
          pass

    def close_eat_def(self):
        self.eat_on_off = 0
        if self.yolo_on_off == 1 and self.danger_on_off == 0:
          self.timer_yolov8.stop()
          self.img_yolo_label.setText('img_yolo')
          self.eat_on_off = 0
          self.yolo_on_off = 0
        else:
          pass

    def start_pose_def(self):
        if self.pose_on_off == 0:
          self.timer_mediapipe.start(250)
          self.timer_mediapipe.timeout.connect(self.mediapipe_run)
          self.pose_on_off = 1
        else:
          pass

    def close_pose_def(self):
        if self.pose_on_off == 1:
          self.timer_mediapipe.stop()
          self.pose_on_off = 0
          self.img_pose_label.setText('img_pose')
        else:
          pass

    def start_danger_def(self):
        self.danger_on_off = 1
        if self.yolo_on_off == 0:
          self.timer_yolov8.start(250)
          self.timer_yolov8.timeout.connect(self.yolov8_run)
          self.yolo_on_off = 1
        else:
          pass

    def close_danger_def(self):
        self.danger_on_off = 0
        if self.yolo_on_off == 1 and self.eat_on_off == 0:
          self.timer_yolov8.stop()
          self.img_yolo_label.setText('img_yolo')
          self.yolo_on_off = 0
        else:
          pass

    def get_img_def(self):
        global img_up
        self.img_l = 'img_new/%d.jpg' % self.write_img_name
        cv2.imwrite(self.img_l, img_up)
        self.write_img_name += 1

    def test_def(self):
        self.stackedWidget.setCurrentIndex(0)
        self.video_stackedWidget.setCurrentIndex(1)
        self.timer_test.start(5)
        self.timer_test.timeout.connect(self.test_run)
        self.test_on_off = 1

    def print_def(self):
        self.stackedWidget.setCurrentIndex(1)
        self.video_stackedWidget.setCurrentIndex(0)
        self.timer_test.stop()
        self.test_on_off = 0

    def s1_add1_def(self):
        self.s1_num += 1
        if self.s1_num > 128:
          self.s1_num = 128
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))
        self.now_edit.append("%s" % self.s1_print)

    def s2_add1_def(self):
        self.s2_num += 1
        if self.s2_num > 128:
          self.s2_num = 128
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_sub1_def(self):
        self.s1_num -= 1
        if self.s1_num < 26:
          self.s1_num = 26
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))

    def s2_sub1_def(self):
        self.s2_num -= 1
        if self.s2_num < 50:
          self.s2_num = 50
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_add2_def(self):
        self.s1_num += 2
        if self.s1_num > 128:
          self.s1_num = 128
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))
        self.now_edit.append("%s" % self.s1_print)

    def s2_add4_def(self):
        self.s2_num += 4
        if self.s2_num > 128:
          self.s2_num = 128
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_sub2_def(self):
        self.s1_num -= 2
        if self.s1_num < 26:
          self.s1_num = 26
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))

    def s2_sub4_def(self):
        self.s2_num -= 4
        if self.s2_num < 50:
          self.s2_num = 50
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_add10_def(self):
        self.s1_num += 10
        if self.s1_num > 128:
          self.s1_num = 128
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))

    def s2_add10_def(self):
        self.s2_num += 10
        if self.s2_num > 128:
          self.s2_num = 128
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_sub10_def(self):
        self.s1_num -= 10
        if self.s1_num < 26:
          self.s1_num = 26
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))

    def s2_sub10_def(self):
        self.s2_num -= 10
        if self.s2_num < 50:
          self.s2_num = 50
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def s1_re_def(self):
        self.s1_num = 77
        self.s1_print = 's1%03d' % self.s1_num
        s.sendto(self.s1_print.encode(), ("10.42.0.189", 9090))

    def s2_re_def(self):
        self.s2_num = 77
        self.s2_print = 's2%03d' % self.s2_num
        s.sendto(self.s2_print.encode(), ("10.42.0.189", 9090))

    def model_ch_def(self):
        if self.model_ch is 0:
          self.now_model_label.setText("监护模式")
          self.model_ch = 1
          self.person_run = 1
          self.previous_eat_number = 0
          self.long_eat_number = 0
          self.eat_number = 0
          self.eat_disappear = 0
          self.find_eat = 0
          self.long_num = 0
        elif self.model_ch is 1:
          self.t_x = 320
          self.t_y = 240
          self.now_model_label.setText("家长模式")
          self.model_ch = 0
          self.person_run = 0

    def timer_init(self):           # 开启定时器运行逻辑程序
        self.timer.start(5)
        self.timer.timeout.connect(self.timer_run)
        self.low_timer.start(2500)
        self.low_timer.timeout.connect(self.low_run)

        '''
        self.timer_yolov8.start(250)
        self.timer_yolov8.timeout.connect(self.yolov8_run)

        self.timer_mediapipe.start(250)
        self.timer_mediapipe.timeout.connect(self.mediapipe_run)
        '''


    def Qt_show_img(self, img, ch):
        show_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        show_img = QImage(show_img, show_img.shape[1], show_img.shape[0], QImage.Format_RGB888)  # 创建Qt图像对象
        if ch is 0:
          self.img_label.setPixmap(QPixmap.fromImage(show_img))       # 显示图像
        if ch is 1:
          self.img_yolo_label.setPixmap(QPixmap.fromImage(show_img))  # 显示图像
        elif ch is 2:
          self.img_pose_label.setPixmap(QPixmap.fromImage(show_img))  # 显示图像
        if ch is 3:
          self.video1.setPixmap(QPixmap.fromImage(show_img))          # 显示图像
        if ch is 4:
          self.video2.setPixmap(QPixmap.fromImage(show_img))          # 显示图像

    def timer_run(self):            # 主要逻辑函数
        # print("ret_down:", ret_down,", ret_up:", ret_up, "\n\n\n\n\n")
        #self.img_up = cv2.imread(img_path_up, 1)
        #self.img_down = cv2.imread(img_path_down, 1)
        # global img_up
        # global img_down
        self.img_up = img_up
        self.img_down = img_down

        if self.model_ch is 1:
            pass
            #self.Qt_show_img(self.img_up, 0)
        elif self.model_ch is 0:
            self.Qt_show_img(self.img_down, 0)

        # self.now_edit.setText("无危险")
        if self.model_ch is 1:
          self.now_edit.clear()
          if self.find_eat is 0:
            self.now_edit.append("现场无易误食物品")
          else:
            self.now_edit.append("现场存在易误食物品")
          if self.danger_number != 0:
            self.now_edit.append("现场存在危险物品！！！")
          if self.eat_disappear is 1 and self.pose_to_eat is 1:
            self.now_edit.append("检测到现场易误食物品消失且存在误食动作！！！")
          else:
            if self.eat_disappear is 1:
              self.now_edit.append("检测到现场易误食物品消失!!!")
            if self.pose_to_eat is 1:
              self.now_edit.append("检测到吃的动作!!!")

        #del self.video_up
        #gc.collect()
        #del self.video_down
        #gc.collect()
        #self.video_down = cv2.VideoCapture('/dev/video4')           # 定义摄像头对象
        #self.video_up = cv2.VideoCapture('/dev/video0')           # 定义摄像头对象

        #self.video_down.release()
        #self.img_up.release()
        #print("self.video_down.isOpened():",self.video_down.isOpened())

    def test_run(self):
        global img_up
        global img_down
        self.video1_img = img_up
        self.video2_img = img_down
        self.video1_img = cv2.resize(self.video1_img, (480, 360))
        self.Qt_show_img(self.video1_img, 3)
        self.video2_img = cv2.resize(self.video2_img, (480, 360))
        self.Qt_show_img(self.video2_img, 4)
        self.s1_label.setText('%d'%self.s1_num)
        self.s2_label.setText('%d'%self.s2_num)

    def low_run(self):
        tt_x = self.t_x
        tt_y = self.t_y

        if self.low_num == 0:
          self.low_num = 1
          if tt_x - 320 >= 25:
            self.print_edit.setText('s11芜湖：%d, %d\n' % (tt_x, tt_y))
            self.s1_sub2_def()
          elif 320 - tt_x >= 25:
            self.print_edit.setText('s12芜湖：%d, %d\n' % (tt_x, tt_y))
            self.s1_add2_def()
        
        if self.low_num == 1:
          self.low_num = 0
          if tt_y -240 >= 25:
            self.print_edit.setText('s21芜湖：%d, %d\n' % (tt_x, tt_y))
            self.s2_sub4_def()
          elif 240 - tt_y >= 25:
            self.print_edit.setText('s22芜湖：%d, %d\n' % (tt_x, tt_y))
            self.s2_add4_def()

    def yolov8_run(self):
        t1 = time.time()
        cv2.imwrite(img_path_down, img_down)
        cv2.imwrite(img_path_up, img_up)
        img_yolo_up = cv2.imread(img_path_up, 1)
        img_person = img_yolo_up.copy()
        predictor = DetectionPredictor(overrides=self.args_yolo)
        predictor.predict_cli()

        if self.eat_on_off is 1 or self.danger_on_off is 1:
          img_yolo = cv2.imread(img_path_down, 1)

          eat_file = open('/home/lilili/eat/yolov8/eat_txt/eat_boxes.txt', 'r+', encoding='utf-8')
          txt = eat_file.read()
          txt = txt.replace('[', ' ')
          txt = txt.replace(']', ' ')
          txt = re.sub(' +', ' ', txt)
          txt = txt.split("\n")
          for tt in txt:
            tt = tt.strip()
            tt = tt.split(" ")
            for t in tt:
              if t != ' ':
                self.box.append(t)

            self.boxes.append(self.box)
            self.box= []
          print("\n\n\n", self.boxes, "\n\n\n")
          
          if len(self.boxes) != 0:
            if self.boxes[0][0] != '':
              # print(self.boxes)
              for box_for in self.boxes:
                if float(box_for[4]) >= 0.7:
                  if self.eat_on_off is 1:
                    if box_for[5] is '2':
                      self.pill_number += 1
                      self.ptLeftTop = (int(box_for[0]), int(box_for[1]))
                      self.ptRightBottom = (int(box_for[2]), int(box_for[3]))
                      cv2.rectangle(img_yolo, self.ptLeftTop, self.ptRightBottom, self.pill_color, self.thickness, self.lineType)
                    elif box_for[5] is '3':
                      self.coin_number += 1
                      self.ptLeftTop = (int(box_for[0]), int(box_for[1]))
                      self.ptRightBottom = (int(box_for[2]), int(box_for[3]))
                      cv2.rectangle(img_yolo, self.ptLeftTop, self.ptRightBottom, self.coin_color, self.thickness, self.lineType)
                  if self.danger_on_off is 1:
                    if box_for[5] is '4':
                      self.knife_number += 1
                      self.ptLeftTop = (int(box_for[0]), int(box_for[1]))
                      self.ptRightBottom = (int(box_for[2]), int(box_for[3]))
                      cv2.rectangle(img_yolo, self.ptLeftTop, self.ptRightBottom, self.knife_color, self.thickness, self.lineType)
                    if box_for[5] is '5':
                      self.clipper_number += 1
                      self.ptLeftTop = (int(box_for[0]), int(box_for[1]))
                      self.ptRightBottom = (int(box_for[2]), int(box_for[3]))
                      cv2.rectangle(img_yolo, self.ptLeftTop, self.ptRightBottom, self.clipper_color, self.thickness, self.lineType)

          else:
            pass
            # self.print_edit.append('not find.')

          self.eat_number = self.pill_number + self.coin_number
          self.danger_number = self.knife_number + self.clipper_number

          self.eat_num.setText(str(self.eat_number))

          self.eat_class_label.setText("药物:%d个\n硬币:%d个\n" % (self.pill_number, self.coin_number))
          self.danger_class_label.setText("水果刀/菜刀:%d个\n剪刀:%d个\n" % (self.knife_number, self.clipper_number))

          if self.model_ch is 0:
            self.now_edit.clear()
            if self.eat_number != 0:
              self.now_edit.append("现场存在易误食物品！请及时处理")
            elif self.eat_number is 0:
              self.now_edit.append("现场已无易误食物品")
            if self.danger_number != 0:
              self.now_edit.append("现场存在危险物品！请及时处理")
            elif self.danger_number is 0:
              self.now_edit.append("现场已无危险物品")
            if self.eat_number is 0 and self.danger_number is 0:
              self.now_edit.setText("无危险，可切换为监护模式")

          elif self.model_ch is 1:
            if self.find_eat is 0:
              if self.eat_number != 0:
                self.find_eat = 1
                self.previous_eat_number = self.eat_number
            elif self.find_eat is 1:
              if self.eat_number < self.previous_eat_number:
                self.eat_disappear = 1
              else:
                self.eat_disappear = 0

          # self.print_edit.setText("%d %d %d" % (self.previous_eat_number, self.eat_number, self.long_num))
          if self.previous_eat_number < self.eat_number:
            self.long_num += 1
            # print("AAAAAA\n")
            if self.long_num >= 4:
              self.long_num = 0
              self.previous_eat_number = self.eat_number
          else:
            self.long_num = 0
          self.person_number = 0
          self.pill_number = 0
          self.coin_number = 0
          self.eat_number = 0
          self.knife_number = 0
          self.clipper_number = 0

          self.boxes = []
          img_yolo = cv2.resize(img_yolo, (480, 360))
          self.Qt_show_img(img_yolo, 1)

          eat_file.truncate(0)
          eat_file.close()

        if self.model_ch is 1:
            predictor = DetectionPredictor(overrides=self.args_person)
            predictor.predict_cli()

            eat_file = open('/home/lilili/eat/yolov8/eat_txt/eat_boxes.txt', 'r+', encoding='utf-8')
            txt = eat_file.read()
            txt = txt.replace('[', ' ')
            txt = txt.replace(']', ' ')
            txt = re.sub(' +', ' ', txt)
            txt = txt.split("\n")
            for tt in txt:
              tt = tt.strip()
              tt = tt.split(" ")
              for t in tt:
                if t != ' ':
                  self.box.append(t)
   
              self.boxes.append(self.box)
              self.box = []
            # print(self.boxes)
            
            if len(self.boxes) != 0:
              if self.boxes[0][0] != '':
                print(self.boxes)
                for box_for in self.boxes:
                  if float(box_for[4]) >= 0.7:
                    if box_for[5] is '0':
                      self.person_number += 1
                      self.ptLeftTop = (int(box_for[0]), int(box_for[1]))
                      self.ptRightBottom = (int(box_for[2]), int(box_for[3]))
                      cv2.rectangle(img_person, self.ptLeftTop, self.ptRightBottom, self.face_color, self.thickness, self.lineType)

                      self.l_x = int(box_for[2]) - int(box_for[0])
                      self.l_y = int(box_for[3]) - int(box_for[1])
                      self.now_xy = self.l_x * self.l_y
                      if self.low_xy <= self.now_xy:
                        self.t_x = (int(box_for[2]) + int(box_for[0])) / 2
                        self.t_y = (int(box_for[3]) + int(box_for[1])) / 2
              else:
                self.t_x = 320
                self.t_y = 240
              self.Qt_show_img(img_person, 0)
              self.low_xy = 0
              self.l_x = 0
              self.l_y = 0
              self.now_xy = 0
            else:
              pass
              # self.print_edit.append('not find.')
   
            self.persom_num.setText(str(self.person_number))
   
   
            self.person_number = 0
            self.pill_number = 0
            self.coin_number = 0
            self.eat_number = 0
            self.knife_number = 0
            self.clipper_number = 0
   
            self.boxes = []
 
            eat_file.truncate(0)
            eat_file.close()
        print("yolo耗时:", time.time() - t1, "s")
   
    def mediapipe_run(self):
        global img_up
        if self.pose_on_off is 1:
          t1 = time.time()
          mp_img = img_up.copy()
          mp_image_hight, mp_image_width, _ = mp_img.shape
          mp_img_RGB = cv2.cvtColor(mp_img, cv2.COLOR_BGR2RGB)

          #处理RGB图像
          results = self.pose_model.process(mp_img_RGB)

          #某一个点的坐标
          if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(mp_img, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS, self.DrawingSpec_point, self.DrawingSpec_line)   # 绘制

            # 嘴巴坐标
            mouth_point = [(results.pose_landmarks.landmark[8].x + results.pose_landmarks.landmark[9].x) / 2 * mp_image_width,
                           (results.pose_landmarks.landmark[8].y + results.pose_landmarks.landmark[9].y) / 2 * mp_image_hight]

            # 左右手的坐标
            left_hand_point = [results.pose_landmarks.landmark[19].x * mp_image_width, results.pose_landmarks.landmark[19].y * mp_image_hight]
            right_hand_point = [results.pose_landmarks.landmark[18].x * mp_image_width, results.pose_landmarks.landmark[18].y * mp_image_hight]

            # 左右手离嘴巴的距离
            left_distance =  math.sqrt((mouth_point[0] - left_hand_point[0]) * (mouth_point[0] - left_hand_point[0]) + (mouth_point[1] - left_hand_point[1]) * (mouth_point[1] - left_hand_point[1]))
            right_distance =  math.sqrt((right_hand_point[0] - mouth_point[0]) * (right_hand_point[0] - mouth_point[0]) + (right_hand_point[1] - mouth_point[1]) * (right_hand_point[1] - mouth_point[1]))
            #print("mouth_point:", mouth_point)
            #print("left_distance:", left_distance)
            #print("right_distance:", right_distance)

            if left_distance <= 150 or right_distance <= 150:
              self.pose_to_eat = 1
              #self.print_edit.append("发现误食动作。")
            else:
              self.pose_to_eat = 0

          mp_img = cv2.resize(mp_img, (480, 360))

          self.Qt_show_img(mp_img, 2)
          print("mediapipe耗时:", time.time() - t1, "s")


if __name__ == '__main__':
    app = QApplication([])      # 创建一个QApplication对象
    window = MyWidget()
    window.show()  # 显示窗口
    app.exec_()  # 程序进入等待循环


