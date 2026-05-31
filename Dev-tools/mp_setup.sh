git clone https://github.com/micropython/micropython.git
cd micropython
git submodule update --init lib/pico-sdk lib/tinyusb
make -C mpy-cross