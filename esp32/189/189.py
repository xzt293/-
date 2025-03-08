import network
import socket
import time
import camera
from machine import Pin, PWM
from machine import Timer


#--------------------------------------------------#
led = Pin(4, Pin.OUT)
def LED_s():   
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)
#--------------------------------------------------#
# LED_s()	# 启动


#--------------------------------------------------#
                    '''
ESP32:  IO0  IO16  IO12
        IO2  IO1   IO0
         0    0     0      255
         0    0     1      254
         0    1     0      253
         0    1     1      252
         1    0     0      251
         1    0     1      250
         1    1     0      249
         1    1     1      248
                    '''

#--------------------------------------------------#


#--------------------------------------------------#
now_x = 320
now_y = 240
s1_out = 77
s2_out = 77

kp = 0.1
ki = 0.1
kd = 0.1

XP = 0
XI = 0
XD = 0
YP = 0
YI = 0
YD = 0

Last_x_Error = 0
Last_y_Error = 0

def PID(x,y):
    global kp, ki, kd, XP, XI, XD, YP, YI, YD, Last_x_Error, Last_y_Error
    x_Error = x - 320
    y_Error = y - 240

    XP  = x_Error
    XI += x_Error
    XD  = x_Error - Last_x_Error

    YP  = y_Error
    YI += y_Error
    YD  = y_Error - Last_y_Error

    Last_x_Error = x_Error
    Last_y_Error = y_Error

    s1_out = kp * XP + ki * XI + kd * XD
    s2_out = kp * YP + ki * YI + kd * YD

    return s1_out, s2_out
# --------------------------------------------------#


#--------------------------------------------------#
# 26——-90° 50——-45° 77——0° 102——45° 128——90°
# s1使用范围为26 - 128
# s2使用范围为50 - 128
pwm1 = PWM(Pin(2),  freq=50, duty=77)   # 左右摆头
time.sleep_ms(100)
pwm2 = PWM(Pin(15), freq=50, duty=77)   # 上下摆头
time.sleep_ms(100)
time.sleep(1)

def servo(s, duty_num):
    if s == 1:
        if duty_num < 26:
            duty_num = 26
        elif duty_num > 128:
            duty_num = 128
        print("舵机1:", duty_num)
        pwm1.duty(duty_num)
    elif s == 2:
        if duty_num < 50:
            duty_num = 50
        elif duty_num > 128:
            duty_num = 128
        print("舵机2:", duty_num)
        pwm2.duty(duty_num)
    else:
        pass
    time.sleep_ms(50)

    return 1
#--------------------------------------------------#


#--------------------------------------------------#
wlan = network.WLAN(network.STA_IF)
# wlan.ifconfig(('192.168.137.189', '255.255.255.0', '192.168.137.1', '192.168.137.1'))
wlan.ifconfig(('10.42.0.189', '255.255.255.0', '10.42.0.1', '10.42.0.1'))
wlan.active(True)

# print(wlan.scan())

if not wlan.isconnected():
    print('正在连接网络...')
    wlan.connect('net', '123456xzt')
    time.sleep(1)
    
    while not wlan.isconnected():
        # LED_s()
        pass
print('wifi连接成功.')
print('network config:', wlan.ifconfig())
my_ip = wlan.ifconfig()[0]
print('my IP:', my_ip)
# LED_s()
#--------------------------------------------------#


#--------------------------------------------------#
# 摄像头初始化
try:
    camera.init(0, format=camera.JPEG)
except Exception as e:
    camera.deinit()
    camera.init(0, format=camera.JPEG)

# 分辨率
camera.framesize(camera.FRAME_HVGA)   # 480*360
# 上翻下翻
camera.flip(1)
#左/右
camera.mirror(1)
# 饱和
camera.saturation(2)   # -2 - 2
# 亮度
camera.brightness(0)   # -2 - 2
# 对比度
camera.contrast(0)   # -2 - 2
# 质量
camera.quality(10)
#10-63数字越小质量越高
# LED_s()
#--------------------------------------------------#


#--------------------------------------------------#
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
s.bind(("0.0.0.0", 9090))

def sendto():
    buf = camera.capture()  # 获取图像数据
    s.sendto(buf, ("10.42.0.1", 9090))  # 向服务器发送图像数据
    # s.sendto(buf, ("192.168.137.1", 9090))  # 向服务器发送图像数据

def spid_run():
    global s1_out, s2_out, now_x, now_y
    s1_out, s2_out = PID(now_x, now_y)
    serv(1, s1_out)
    serv(2, s2_out)

tim = Timer(0)#调用定时器
tim.init(period = 3,mode = Timer.PERIODIC,callback = lambda x:sendto())
tim_pid = Timer(1)#调用定时器
tim.init(period = 1000,mode = Timer.PERIODIC,callback = lambda x:spid_run())
#--------------------------------------------------#

# s.sendto(my_ip, ("192.168.137.1", 9090))
# time.sleep(0.2)
print("run!")
while True:
    word = s.recvfrom(8)[0].decode('UTF-8')
    print(word)
    if word[0] == 's':
        if word[1] == 'p':
            now_x = int(word[2:4])
            now_y = int(word[5:8])
        if word[1] == '1':
            now_x = 320
            now_y = 240
            servo(int(word[1]), int(word[2:5]))
            # print("舵机%d: %d\n" % (int(word[1]), int(word[2:5])))
        if word[1] == '2':
            now_x = 320
            now_y = 240
            servo(int(word[1]), int(word[2:5]))
            # print("舵机%d: %d\n" % (int(word[1]), int(word[2:5])))
            
