from app.controller import library
from machine import Pin
import time
apex = library()

def setup():
    apex.newfile('data.csv')
    apex.log_headers()
    apex.calibrate({'pressure_hpa': 0})

def loop():
    data = apex.read_sensor()
    if data != None:
        print(data)

apex.run(setup, loop)