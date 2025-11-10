import machine
import utime
import network
import urequests
import json

# === Wi-Fi 연결 ===
ssid = "Wokwi-GUEST"
password = ""

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
print("Connecting to Wi-Fi...", end="")
sta_if.connect(ssid, password)
while not sta_if.isconnected():
    print(".", end="")
    utime.sleep(0.1)
print("\nWi-Fi connected! IP:", sta_if.ifconfig())

# === Webhook API URL ===
API_URL = "https://hooks.zapier.com/hooks/catch/25312579/usj5m2p/"

# === 초음파 핀 설정 ===
TRIGGER_PIN = machine.Pin(4, machine.Pin.OUT)
ECHO_PIN    = machine.Pin(15, machine.Pin.IN)

# === 타이머 변수 ===
timer_running     = False
timer_start       = 0
time_rate_per_hour = 6000  # KRW/hour

# === 거리 측정 함수 ===
def get_distance(timeout_us=30000):
    TRIGGER_PIN.value(0)
    utime.sleep_us(2)
    TRIGGER_PIN.value(1)
    utime.sleep_us(10)
    TRIGGER_PIN.value(0)

    start_wait = utime.ticks_us()
    pulse_start = None
    pulse_end = None

    # Echo가 HIGH 될 때까지 대기
    while ECHO_PIN.value() == 0:
        if utime.ticks_diff(utime.ticks_us(), start_wait) > timeout_us:
            return -1  # timeout
        pulse_start = utime.ticks_us()

    # Echo가 LOW 될 때까지 대기
    while ECHO_PIN.value() == 1:
        if utime.ticks_diff(utime.ticks_us(), start_wait) > timeout_us:
            return -1  # timeout
        pulse_end = utime.ticks_us()

    if pulse_start is None or pulse_end is None:
        return -1  # 안전 장치

    pulse_duration = utime.ticks_diff(pulse_end, pulse_start)
    distance = pulse_duration * 0.0343 / 2  # cm

    # 최소 거리 제한 (2cm 미만이면 2cm로 처리)
    if distance < 2:
        distance = 2

    return distance



# === 메인 루프 ===
while True:
    distance = get_distance()
    
    if distance == -1:
        print("Distance: less than 2cm")
    else:
        print("Distance:", round(distance,2), "cm")

    # 30cm 이하이면 타이머 시작
    if distance <= 30 and not timer_running:
        timer_running = True
        timer_start = utime.ticks_ms()
        print("Timer started")

    # 타이머 진행 중
    if timer_running:
        elapsed_ms = utime.ticks_diff(utime.ticks_ms(), timer_start)
        print("Timer running:", round(elapsed_ms/1000,2), "seconds")

        # 거리 > 30cm이면 타이머 종료 및 Webhook 전송
        if distance > 30:
            timer_running = False
            elapsed_sec = elapsed_ms / 1000
            elapsed_hour = elapsed_sec / 3600
            cost = elapsed_hour * time_rate_per_hour
            print("Timer stopped")
            print("Total elapsed time:", round(elapsed_sec,2), "seconds")
            print("Charge: approx", round(cost,2), "KRW")

            # Webhook.site로 JSON 전송
            data = {"elapsed_sec": round(elapsed_sec,2), "cost": round(cost,2)}
            try:
                response = urequests.post(API_URL, json=data)
                print("Sent data to Webhook, status code:", response.status_code)
                response.close()
            except Exception as e:
                print("Failed to send data:", e)

    utime.sleep(1)

