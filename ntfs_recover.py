import pytsk3
import sys
import os
import uuid          # <- still used only for internal bookkeeping in the list, not for filenames
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

class DeletedFile:
    def __init__(self, name, path):
        self.name = name
        self.path = path

class RecoverApp:
    def __init__(self, root, drive_path):
        self.root = root
        self.root.title("Deleted File Recovery")
        self.drive_path = drive_path
        self.img = pytsk3.Img_Info(drive_path)
        self.fs = pytsk3.FS_Info(self.img)
        self.deleted_files = []
        self.check_vars = []

        self.create_widgets()
        self.walk_directory("/")

    # ───────────────────────── GUI ──────────────────────────
    def create_widgets(self):
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.pack(fill="both", expand=True)

        self.list_label = ttk.Label(self.frame, text="Select Deleted Files to Recover:")
        self.list_label.pack(anchor="w")

        self.canvas = tk.Canvas(self.frame)
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.recover_button = ttk.Button(self.frame, text="Recover Selected", command=self.recover_selected)
        self.recover_button.pack(pady=10)

    # ──────────────── Filesystem Traversal ────────────────
    def walk_directory(self, directory):
        visited_dirs = set()
        system_dirs = ["$RECYCLE.BIN", "System Volume Information", "$Extend"]

        def _walk(dir_path):
            if any(sys_dir in dir_path for sys_dir in system_dirs):
                return

            norm_path = os.path.normpath(dir_path)
            if norm_path in visited_dirs:
                return
            visited_dirs.add(norm_path)

            try:
                dir_obj = self.fs.open_dir(path=dir_path)
                for entry in dir_obj:
                    try:
                        name = entry.info.name.name.decode()
                        if name in [".", ".."]:
                            continue

                        full_path = dir_path.rstrip("/") + "/" + name
                        if entry.info.meta is None and entry.info.name:
                            # Deleted file found
                            self.deleted_files.append(DeletedFile(name, full_path))
                            var = tk.BooleanVar()
                            ttk.Checkbutton(self.scroll_frame, text=full_path, variable=var).pack(anchor="w")
                            self.check_vars.append((var, full_path, name))
                        elif entry.info.meta and entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                            _walk(full_path)
                    except Exception as e:
                        print(f"⚠️ Entry error: {e}")
            except Exception as e:
                print(f"⚠️ Directory access error ({dir_path}): {e}")

        _walk(directory)

    # ────────────────── Recovery Logic ────────────────────
    def recover_selected(self):
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            return

        recovered = 0
        for var, path, name in self.check_vars:
            if not var.get():
                continue
            try:
                # ---- OPEN THE FILE IN THE IMAGE ----
                file_obj = self.fs.open(path)
                file_data = file_obj.read_random(0, file_obj.info.meta.size)

                # ---- DETERMINE A SAFE OUTPUT NAME ----
                output_path = os.path.join(output_folder, name)
                if os.path.exists(output_path):
                    base, ext = os.path.splitext(name)
                    i = 1
                    while True:
                        alt_name = f"{base}_{i}{ext}"
                        output_path = os.path.join(output_folder, alt_name)
                        if not os.path.exists(output_path):
                            break
                        i += 1

                # ---- WRITE THE RECOVERED CONTENT ----
                with open(output_path, "wb") as f:
                    f.write(file_data)
                recovered += 1
            except Exception as e:
                print(f"⚠️ Could not recover {name}: {e}")

        messagebox.showinfo("Recovery Complete", f"Recovered {recovered} file(s) to:\n{output_folder}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gui_recover.py <disk_image_path>")
        sys.exit(1)

    drive_path = sys.argv[1]
    root = tk.Tk()
    RecoverApp(root, drive_path)
    root.mainloop()
