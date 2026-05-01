@echo off
mpremote rm -r :
mpremote cp -r Pico-code\* :
mpremote reset
ping -n 1 -w 500 127.0.0.1 >nul
mpremote repl