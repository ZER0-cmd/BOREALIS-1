# Upload desired changes in micropython/ports/rp2/modules

cp -r Pico-code/app Pico-code/pictures Pico-code/drivers Dev-tools/micropython/ports/rp2/modules/
make -C Dev-tools/micropython/ports/rp2 BOARD=RPI_PICO
cp Dev-tools/micropython/ports/rp2/build-RPI_PICO/firmware.uf2 Dev-tools/apex_firmware.uf2