from app.controller import library
from machine import Pin
import time
main = library()

def setup():
    # while not main.log_ready:
    main.newfile('data.csv')
    main.log_headers()

def loop():
    data = main.read_sensor()
    if data != None:
        print(data)
    main.log_data(data)

main.run(setup, loop)