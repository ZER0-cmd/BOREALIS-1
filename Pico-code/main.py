from app.controller import Library
from machine import Pin
import time
apex = Library()

def setup():
    apex.newfile('data.csv')
    apex.log_headers()

def loop():
    data = apex.read_sensor()
    if data != None:
        print(data)
        apex.log_data(data)

apex.run(setup, loop)