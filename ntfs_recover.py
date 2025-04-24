import pytsk3
import sys
import os
import uuid

def recover_deleted_files(drive_path, output_folder):
    img = pytsk3.Img_Info(drive_path)
    fs = pytsk3.FS_Info(img)

    visited_dirs = set()
    system_dirs = ["$RECYCLE.BIN", "System Volume Information", "$Extend"]

    def walk_directory(directory):
        if any(sys_dir in directory for sys_dir in system_dirs):
            return

        normalized_dir = os.path.normpath(directory)
        if normalized_dir in visited_dirs:
            return
        visited_dirs.add(normalized_dir)

        try:
            dir_obj = fs.open_dir(path=directory)
            for entry in dir_obj:
                try:
                    name = entry.info.name.name.decode()
                    if name in [".", ".."]:
                        continue

                    if entry.info.meta is None and entry.info.name:
                        print(f"🪦 Found deleted file: {name}")
                        file_path = directory.replace("\\", "/") + "/" + name
                        try:
                            file_obj = fs.open(file_path)
                            file_data = file_obj.read_random(0, file_obj.info.meta.size)
                            unique_id = uuid.uuid4().hex[:6]
                            output_path = os.path.join(output_folder, f"RECOVERED_{unique_id}_{name}")
                            with open(output_path, "wb") as f:
                                f.write(file_data)
                            print(f"✅ Recovered to: {output_path}")
                        except Exception as e:
                            print(f"⚠️ Cannot recover content of {name}: {e}")
                except Exception as e:
                    print(f"⚠️ Error processing entry: {e}")

                if entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                    subfolder_path = directory.replace("\\", "/") + "/" + name
                    walk_directory(subfolder_path)

        except Exception as e:
            print(f"⚠️ Error accessing directory {directory}: {e}")

    walk_directory("/")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test.py <drive> <output_folder>")
        sys.exit(1)

    drive_path = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)

    recover_deleted_files(drive_path, output_folder)
