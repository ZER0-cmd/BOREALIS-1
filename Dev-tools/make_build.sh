# Upload desired changes in micropython/ports/rp2/modules

cp -r Pico-code/app Pico-code/drivers Dev-tools/micropython/ports/rp2/modules/
cp Dev-tools/uf2-changes/ui.py Dev-tools/micropython/ports/rp2/modules/
python Dev-tools/csv2py.py Dev-tools/micropython/ports/rp2/modules/pictures Pico-code/pictures

make -C Dev-tools/micropython/ports/rp2 BOARD=RPI_PICO
cp Dev-tools/micropython/ports/rp2/build-RPI_PICO/firmware.uf2 Dev-tools/apex_firmware.uf2