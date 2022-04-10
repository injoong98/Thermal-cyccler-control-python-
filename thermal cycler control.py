# 쿨링펜 제어 관련 참고자려 링크 : https://blog.naver.com/cosmosjs/222549963664
# MLX90614 샌서관련 참고자료 링크 : https://blog.naver.com/youseok0/222389919984
# PWM 제어 관련 참고자료 링크 : https://rasino.tistory.com/328

import RPi.GPIO as GPIO
from time import sleep

from smbus2 import SMBus            # I2C 통신 모듈
from mlx90614 import mlx90614       # MLX90614 센서 모듈


def printStatusMessage(total_cycle, pelt_pwmOff, fan_pinState) :
     # 상태메시지 출력
    print("Cooling start")
    print("current cycle : ", str(total_cycle), "peltier module PWM : ", str(pelt_pwmOff), "   fan state : ", str(fan_pinState))


def tempControlByPWM(current_temp, goal_temp, pelt_pwm, mode) :
    
    error = goal_temp - current_temp # 목표온도 - 현재온도
    error_max = 94 - 25  # PCR과정 중 온도차의 최대값 [DNA denaturation temp - 상온]
    temp_range = 110 - 25  # 펠티어 온도 최대값 - 최솟값

    goal_pwm = (goal_temp - 25) / temp_range * 100  # 목표 PWM 수치 [목표온도가 25도이면 PWM 0, 110도이면 PWM 100]

    if mode == "heating":
        pwm_value = goal_pwm + (100 - goal_pwm) * (error / error_max) # heating시 PWM 값 [error가 크면 클수록 목표 PWM 수치보다 더 큰 값을 입력]
    elif mode == "cooling":
        pwm_value = goal_pwm * (1 + (error / error_max)) # cooling시 PWM 값 [error가 크면 클수록 목표 PWM 수치보다 더 낮은 값을 입력]

    pelt_pwm.ChangeDutyCycle(pwm_value)


    global step_flag
    global step_time

    # 목표온도 도달 시 step_flag로 표시한 뒤 지속시간 체크
    if current_temp == goal_temp and step_flag == False:
        step_flag = True
    elif step_flag == ture:
        step_time = step_time + 0.01



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


    global step_time        # 각 스텝별 진행시간
    global step_flag        # 각 스텝 진행중인지 여부
    step_now = 1       # 현재 스텝 [1. denaturation  2. primer annealing  3. primer extension]
    step_time = 0
    step_flag = False


    while True:

        # print("Ambient Temperature :", sensor.get_ambient())        # 주변온도 출력
        print("Object Temperature :", sensor.get_object_1())        # 대상물체온도 출력

        current_temp = sensor.get_object_1()    # 현재 대상온도 값


        # 30사이클 도달 시 반복문 중단
        if total_cycle == 30:
            print("thermal cycle complete")
            break


        # PCR단계에 따른 목표온도 설정
        if step_now == 1:
            # denaturation 단계 / 94도 까지 가열
            tempControlByPWM(current_temp, 94, pelt_pwm, 'heating')
            if step_time == 4:
                step_flag = False
                step_time = 0
                step_now = 2
        elif step_now == 2:
            # primer annealing 단계 / 50도 까지 냉각
            tempControlByPWM(current_temp, 50, pelt_pwm, 'cooling')
            if step_time == 4:
                step_flag = False
                step_time = 0
                step_now = 3
        elif step_now == 3:
            # primer extension 단계 / 70도 까지 가열
            tempControlByPWM(current_temp, 70, pelt_pwm, 'heating')
            if step_time == 4:
                step_flag = False
                step_time = 0
                step_now = 1
                total_cycle = total_cycle + 1
        else:
            print("unexpected situation occurs")
        
        sleep(0.01)      # 반복문 0.01초 주기

except KeyboardInterrupt:
    print("Exit pressed Ctrl+C")

finally:
    print("CleanUp")
    GPIO.cleanup()
    print("End of program")
