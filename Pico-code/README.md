Functionalities:

Guide:

How to setup pico:

How to setup vscode:

How to upload code to pico:

enter these commands on the terminal

mpremote connect COMx fs cp main.py :main.py
mpremote connect COMx fs cp config.py :config.py
mpremote connect COMx fs cp -r app :/
mpremote connect COMx fs cp -r drivers :/
mpremote connect COMx fs cp -r scripts :/
mpremote connect COMx reset

make sure mpremote is installed first!
