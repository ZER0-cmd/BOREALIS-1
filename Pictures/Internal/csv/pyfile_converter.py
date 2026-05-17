# csv_to_py.py
import csv, os, glob

os.makedirs("Pico-code/pictures", exist_ok=True)

for csv_path in glob.glob("pictures/*.csv"):
    name = os.path.splitext(os.path.basename(csv_path))[0]
    pixels = []
    dim = (0, 0)

    with open(csv_path, newline="") as f:
        for row in csv.reader(f):
            row = [r.strip() for r in row]
            if len(row) == 2:
                dim = (int(row[0]), int(row[1]))
            elif len(row) == 3:
                pixels.append(int(row[0]))
                pixels.append(int(row[1]))
                pixels.append(int(row[2]))

    with open(f"Pico-code/pictures/{name.replace(' ', '')}.py", "w") as f:
        f.write(f"DIM = {dim}\n")
        f.write(f"PIXELS = bytes({pixels})\n")

    print(f"Converted {csv_path} ({len(pixels)//3} pixels)")