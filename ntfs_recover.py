import pytsk3
import sys
import os

def recover_deleted_files(drive_path, output_folder):
    img = pytsk3.Img_Info(drive_path)
    fs = pytsk3.FS_Info(img)

    directory = fs.open_dir(path="/")
    for entry in directory:
        try:
            if entry.info.meta is None and entry.info.name:
                name = entry.info.name.name.decode()
                print(f"🪦 Found deleted file: {name}")
                # Try reading file content via data attribute
                try:
                    file_obj = fs.open(name)
                    file_data = file_obj.read_random(0, file_obj.info.meta.size)
                    output_path = os.path.join(output_folder, f"RECOVERED_{name}")
                    with open(output_path, "wb") as f:
                        f.write(file_data)
                    print(f"✅ Recovered to: {output_path}")
                except Exception as e:
                    print(f"⚠️ Cannot recover content of {name}: {e}")
        except Exception as e:
            continue

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test.py <drive> <output_folder>")
        sys.exit(1)

    drive_path = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)

    recover_deleted_files(drive_path, output_folder)