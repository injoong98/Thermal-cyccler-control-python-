# 쿨링펜 제어 관련 참고자려 링크 : https://blog.naver.com/cosmosjs/222549963664
# MLX90614 샌서관련 참고자료 링크 : https://blog.naver.com/youseok0/222389919984
# PWM 제어 관련 참고자료 링크 : https://rasino.tistory.com/328

import RPi.GPIO as GPIO
from time import sleep

from smbus2 import SMBus            # I2C 통신 모듈
from mlx90614 import mlx90614       # MLX90614 센서 모듈


try:
    tempOn = 90         # Cooling 시작 기준점 온도
    tempOff = 60         # Heating 시작 기준점 온도

    fan_pinNo = 14      # 펜 pin 번호
    fan_pinState = False    # 펜 작동상태

    pelt_pinNo = 18         # 펠티어모듈 pin 번호
    pelt_pwmOn = 70          # Heating 시 펠티어모듈의 PWM 수치
    pelt_pwmOff = 0          # Cooling 시 펠티어모듈의 PWM 수치

    # GPIO 핀 번호 세팅
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(fan_pinNo, GPIO.OUT)
    GPIO.setup(pelt_pinNo, GPIO.OUT)
    
    pelt_pwm = GPIO.PWM(pelt_pinNo, 100)        # 펠티어모듈 PWM 설정
    pelt_pwm.start(0)           # 초기 펠티어모듈 PWM 0으로 시작


    I2C_adress = 0x5A       # I2C Bus의 mlx센서 주소 값
    bus = SMBus(1)          # I2C 버스 설정
    sensor = mlx90614(bus, address=I2C_adress)          # mlx센서 통신 설정
    
    total_cycle = 0         # 총 사이클 진행 수

    while True:

        print("Ambient Temperature :", sensor.get_ambient())        # 주변온도 출력
        print("Object Temperature :", sensor.get_object_1())        # 대상물체온도 출력

        temp = sensor.get_object_1()    # 현재 대상온도 값

        # 온도가 상한선을 넘어갔을 때 cooling 시작
        if temp > tempOn and not fan_pinState:  
            # 펠티어 pwm off 설정
            pelt.pwm.ChangeDutyCycle(pelt_pwmOff)
            # 펜 off 설정
            fan_pinState = not fan_pinState
            GPIO.output(fan_pinNo, fan_pinState)
            # 상태메시지 출력
            print("Cooling start")
            print("current cycle : ", str(total_cycle), "peltier module PWM : ", str(pelt_pwmOff), "   fan state : ", str(fan_pinState))

        # 온도가 하한선을 넘어갔을 때 heating 시작
        elif temp < tempOff and fan_pinState:
            # 사이클 수 +1
            total_cycle = total_cycle + 1
            # 사이클 30 초과시 반복문 중단
            if total_cycle == 31:
                print("thermal cycle complete")
                break
            # 펠티어 pwm on 설정
            pelt.pwm.ChangeDutyCycle(pelt_pwmOn)
            # 펜 on 설정
            fan_pinState = not fan_pinState
            GPIO.output(fan_pinNo, fan_pinState)
            # 상태메시지 출력
            print("Heating start")
            print("current cycle : ", str(total_cycle), "peltier module PWM : ", str(pelt_pwmOn), "   fan state : ", str(fan_pinState))
        
        sleep(0.1)      # 반복문 0.1초 주기

except KeyboardInterrupt:
    print("Exit pressed Ctrl+C")

finally:
    print("CleanUp")
    GPIO.cleanup()
    print("End of program")
