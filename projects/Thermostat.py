from time import sleep
from datetime import datetime
import board
import adafruit_ahtx0
from gpiozero import Button, PWMLED
import RPi.GPIO as GPIO

LCD_RS = 27
LCD_E  = 22
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18

RED_LED = 17
BLUE_LED = 4

BLUE_BUTTON = 24
RED_BUTTON = 25
YELLOW_BUTTON = 12

set_point = 72
state = "off"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

red = PWMLED(RED_LED)
blue = PWMLED(BLUE_LED)

mode_btn = Button(BLUE_BUTTON, pull_up=True, bounce_time=0.2)
up_btn = Button(RED_BUTTON, pull_up=True, bounce_time=0.2)
down_btn = Button(YELLOW_BUTTON, pull_up=True, bounce_time=0.2)

i2c = board.I2C()
sensor = adafruit_ahtx0.AHTx0(i2c)

LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

def lcd_toggle():
    sleep(0.0005)
    GPIO.output(LCD_E, True)
    sleep(0.0005)
    GPIO.output(LCD_E, False)
    sleep(0.0005)

def lcd_byte(bits, mode):
    GPIO.output(LCD_RS, mode)

    for pin in [LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
        GPIO.output(pin, False)

    if bits & 0x10: GPIO.output(LCD_D4, True)
    if bits & 0x20: GPIO.output(LCD_D5, True)
    if bits & 0x40: GPIO.output(LCD_D6, True)
    if bits & 0x80: GPIO.output(LCD_D7, True)
    lcd_toggle()

    for pin in [LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
        GPIO.output(pin, False)

    if bits & 0x01: GPIO.output(LCD_D4, True)
    if bits & 0x02: GPIO.output(LCD_D5, True)
    if bits & 0x04: GPIO.output(LCD_D6, True)
    if bits & 0x08: GPIO.output(LCD_D7, True)
    lcd_toggle()

def lcd_init():
    for pin in [LCD_E, LCD_RS, LCD_D4, LCD_D5, LCD_D6, LCD_D7]:
        GPIO.setup(pin, GPIO.OUT)

    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    sleep(0.01)

def lcd_message(msg, line):
    msg = msg[:LCD_WIDTH].ljust(LCD_WIDTH)
    lcd_byte(line, LCD_CMD)
    for char in msg:
        lcd_byte(ord(char), LCD_CHR)

def toggle_mode():
    global state
    if state == "off":
        state = "heat"
    elif state == "heat":
        state = "cool"
    else:
        state = "off"

def raise_temp():
    global set_point
    set_point += 1

def lower_temp():
    global set_point
    set_point -= 1

mode_btn.when_pressed = toggle_mode
up_btn.when_pressed = raise_temp
down_btn.when_pressed = lower_temp

lcd_init()
count = 0

try:
    while True:
        temp_c = sensor.temperature
        temp_f = (temp_c * 9 / 5) + 32

        red.off()
        blue.off()

        if state == "heat":
            if temp_f < set_point:
                red.pulse()
            else:
                red.on()

        elif state == "cool":
            if temp_f > set_point:
                blue.pulse()
            else:
                blue.on()

        lcd_message(datetime.now().strftime("%m/%d %H:%M"), LCD_LINE_1)

        if count % 2 == 0:
            lcd_message(f"Temp:{temp_f:.1f}F", LCD_LINE_2)
        else:
            lcd_message(f"{state} Set:{set_point}F", LCD_LINE_2)

        if count % 15 == 0:
            print(f"{state},{temp_f:.1f},{set_point}")

        count += 1
        sleep(2)

except KeyboardInterrupt:
    red.off()
    blue.off()
    lcd_byte(0x01, LCD_CMD)
    GPIO.cleanup()
