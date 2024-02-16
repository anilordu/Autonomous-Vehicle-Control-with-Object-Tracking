import cv2
import RPi.GPIO as GPIO
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

# GPIO numaralandırma tanımlamaları
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Pin tanımlamaları
pwm1 = 24
pwm2 = 23
pwm3 = 17
pwm4 = 18

# GPIO pin kurulumları
GPIO.setup(pwm1, GPIO.OUT)
GPIO.setup(pwm2, GPIO.OUT)
GPIO.setup(pwm3, GPIO.OUT)
GPIO.setup(pwm4, GPIO.OUT)
# PWM kurulumları
sag_ileri = GPIO.PWM(pwm1, 100)
sag_geri = GPIO.PWM(pwm2, 100)
sol_ileri = GPIO.PWM(pwm3, 100)
sol_geri = GPIO.PWM(pwm4, 100)

sag_ileri.start(0)
sag_geri.start(0)
sol_ileri.start(0)
sol_geri.start(0)
# motorların durması için kullanılacak fonksiyon
def dur():
    sag_ileri.ChangeDutyCycle(0)
    sag_geri.ChangeDutyCycle(0)
    sol_ileri.ChangeDutyCycle(0)
    sol_geri.ChangeDutyCycle(0)
# motorların kontrolü için kullanılacak fonksiyon
def motor_kontrol(x, a):
    if a > 50000:
        sag_ileri.ChangeDutyCycle(0)
        sag_geri.ChangeDutyCycle(38)
        sol_ileri.ChangeDutyCycle(0)
        sol_geri.ChangeDutyCycle(38)
    elif a < 30000:
        if x > 50:
            sag_ileri.ChangeDutyCycle(0)
            sag_geri.ChangeDutyCycle(60)
            sol_ileri.ChangeDutyCycle(60)
            sol_geri.ChangeDutyCycle(0)
        
        elif x < -50:
            sag_ileri.ChangeDutyCycle(60)
            sag_geri.ChangeDutyCycle(0)
            sol_ileri.ChangeDutyCycle(0)
            sol_geri.ChangeDutyCycle(60)
        
        else :
            sag_ileri.ChangeDutyCycle(50)
            sag_geri.ChangeDutyCycle(0)
            sol_ileri.ChangeDutyCycle(50)
            sol_geri.ChangeDutyCycle(0)
    else:
        dur()

# nesnenin görüntü içinde yakalanması için kullanılacak fonksiyon
def nesne_takibi():
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))

    time.sleep(0.1)

    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])

    ekran_merkez_x = camera.resolution[0] // 2
    ekran_merkez_y = camera.resolution[1] // 2

    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        image = frame.array

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, lower_blue, upper_blue)

        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        #konturların bulunması
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # bulunan konturların dikdörtgen içine alınması
        if contours:
            for contour in contours:
                if cv2.contourArea(contour) > 1000:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)
                    
                    x_ekseni = x + (w // 2) - ekran_merkez_x
                    y_ekseni = ekran_merkez_y - (y + (h // 2))
                    alan = w * h

                    print("Koordinatlar(", x_ekseni,",", y_ekseni ,"), Dikdortgen Alanı:", alan)
                    motor_kontrol(x_ekseni, alan)
        # görüntüde cisim yoksa motorların durması
        else:
            dur()

        cv2.imshow("Nesne Takibi", image)
        # "q" tuşuna basılınca programı ve motorları durdur
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        rawCapture.truncate(0)
        
    dur()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    nesne_takibi()
