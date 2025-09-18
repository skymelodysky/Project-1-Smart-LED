import os
import time
import neopixel
import adafruit_connection_manager
import board
import busio

from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
from analogio import AnalogIn
from digitalio import DigitalInOut

import adafruit_minimqtt.adafruit_minimqtt as MQTT



try:
    from secrets import secrets
except ImportError:
    print("MQTT secrets are kept in secrets.py, please add them there!")
    raise

cs = DigitalInOut(board.GP17)
spi_bus = busio.SPI(board.GP18, MOSI=board.GP19, MISO=board.GP16)


eth = WIZNET5K(spi_bus, cs)


light_button_feed = secrets["aio_username"] + "/feeds/light"
brightness_feed = secrets["aio_username"] + "/feeds/brightness"
rainbow_feed = secrets["aio_username"] + "/feeds/rainbow-mode"
color_feed = secrets["aio_username"] + "/feeds/led-color"



def connected(client, userdata, flags, rc):
    client.subscribe(light_button_feed)
    client.subscribe(rainbow_feed)
    client.subscribe(color_feed)


def disconnected(client, userdata, rc):
    print("Disconnected from Adafruit IO!")



num_pixels = 12
pixels = neopixel.NeoPixel(board.GP0, num_pixels)

brightness = AnalogIn(board.GP26) 


rainbowColorList = [
    (255, 0, 0), (255, 127, 0), (255, 165, 0), 
    (255, 255, 0), (0, 255, 0), (0, 255, 255), 
    (0, 0, 255), (75, 0, 130), (148, 0, 211), 
    (128, 0, 128)
]


def message(client, topic, message):
    global Turn_on ,Led_looping_num ,Color_looping_num, rainbowMode, color, rainbowMode

    if topic == light_button_feed:
        if message == "1":
            print("Turn on the LEDs")
            Led_looping_num = 0
            Color_looping_num = 0
            Turn_on = True
        else:
            Turn_on = False
            print("Turn off the LEDs")
                   
    elif topic == rainbow_feed:
        if message == "1":
            rainbowMode = True
        else:
            rainbowMode = False
            
    elif topic == color_feed:
        color = message
    
    

def publish(client, userdata, topic, pid):
    print("Published to {0} with PID {1}".format(topic, pid))
    if userdata is not None:
        print("Published User dat: ", end="")
        print(userdata)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    return (r, g, b)

pool = adafruit_connection_manager.get_radio_socketpool(eth)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)


mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    is_ssl=True,
    socket_pool=pool,
    ssl_context=ssl_context,
)


mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message
mqtt_client.on_publish = publish


print("Connecting to Adafruit IO...")
mqtt_client.connect()

mqtt_client.publish(light_button_feed, "0")
mqtt_client.publish(rainbow_feed, "1")
mqtt_client.publish(color_feed, "#FFFFFF")
Turn_on = False
rainbowMode = True
Led_looping_num = 0
Color_looping_num = 0
color = "#FFFFFF"
last_published_brightness = -1
threshold = 0.1

while True:

    mqtt_client.loop()
    if Turn_on :
        current_brightness = brightness.value / 65536
        pixels.brightness = current_brightness

    
        if last_published_brightness == -1 or abs(current_brightness - last_published_brightness) >= threshold:
            mqtt_client.publish(brightness_feed, int(current_brightness * 100))  
            last_published_brightness = current_brightness  


        if rainbowMode:
            pixels.brightness = brightness.value/65536
            mqtt_client.publish(brightness_feed, int(brightness.value/65536 * 100))
            
            pixels[Led_looping_num % num_pixels] = rainbowColorList[len(rainbowColorList)-1-(Color_looping_num % len(rainbowColorList))]
            Led_looping_num+=1
            Color_looping_num+=1
        else:
  
            pixels.fill(hex_to_rgb(color))
    else:
        pixels.fill((0,0,0))

    time.sleep(0.5)
        
        
        

