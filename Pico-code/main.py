from app.controller import library
from machine import Pin
import time
main = library()

def setup():
    main.newfile('data.csv')
    main.log_headers()

def loop():
    data = main.read_sensor()
    print(data)
    # print(main.ready)
    main.log_data(data)

main.run(setup, loop)