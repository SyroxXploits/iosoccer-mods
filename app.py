# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                                                                          ║
# ║                Please do not re-upload as your own app                   ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                                                                          ║
# ║                        Made by SyRoX                                     ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                                                                          ║
# ║                        Leave a like on the github                        ║
# ║                                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import os
import json
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import ttkbootstrap as tb
import tempfile
import zipfile
import threading
import shutil
import subprocess
import platform
import sys
from packaging import version
import hashlib

## App version check
APP_VERSION = "1.0.5"
UPDATE_INFO_URL = "https://raw.githubusercontent.com/SyroxXploits/iosoccer-mods/refs/heads/main/modrepo/app_version.json"

## App window config
class ModManagerApp:
    def __init__(self):
        self.MOD_INDEX_URL = "https://raw.githubusercontent.com/SyroxXploits/iosoccer-mods/refs/heads/main/modrepo/mods_index.json"
        self.thumbnails = {}
        self.search_loaded = False
        self.app = tb.Window(themename="darkly")
        self.app.title("IOsoccer Mod Manager")
        self.app.geometry("920x700")
        self.game_path_var = tk.StringVar()
        self.CONFIG_FILE = "config.json"
        self.load_config()
        self.installed_mods = []
        self.search_var = tk.StringVar()
        self.sort_option = tk.StringVar(value="Name")
        self.setup_ui()
        self.load_available_mods(force=True)
        self.thumbnails = {}
        self.cache_dir = ".cache"
        os.makedirs(self.cache_dir, exist_ok=True)

        # Load placeholder
        placeholder_path = os.path.join(self.cache_dir, "placeholder.png")
        if not os.path.exists(placeholder_path):
            try:
                url = "https://i.imgur.com/wB29VAF.png"  # Replace with your own if desired
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, timeout=5, headers=headers)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGBA")
                image = image.resize((128, 72), Image.Resampling.LANCZOS)
                self.placeholder_img = ImageTk.PhotoImage(image)
            except Exception as e:
                print(f"Failed to load placeholder image: {e}")
                self.placeholder_img = None
        



## Check for update
    def check_for_updates(self):
            def _check():
                try:
                    resp = requests.get(UPDATE_INFO_URL, timeout=10)
                    resp.raise_for_status()
                    data = resp.json()
                    latest_version = data.get("version", "")
                    download_url = data.get("download_url", "")

                    if self.is_version_newer(latest_version, APP_VERSION):
                        if messagebox.askyesno("Update Available",
                            f"A new version ({latest_version}) is available. Update now?"):
                            self.download_and_apply_update(download_url)
                except Exception as e:
                    print(f"Update check failed: {e}")

            threading.Thread(target=_check, daemon=True).start()

    def is_version_newer(self, latest, current):
            try:
                return version.parse(latest) > version.parse(current)
            except Exception:
                return False

    def download_and_apply_update(self, url):
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            temp_dir = tempfile.mkdtemp(prefix="iosoccer_update_")
            archive_path = os.path.join(temp_dir, "update_archive")

            try:
                # Download the archive
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(archive_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                # Detect archive type
                with open(archive_path, "rb") as f:
                    file_start = f.read(8)

                if file_start.startswith(b'PK'):
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(app_dir)
                elif file_start.startswith(b'Rar!\x1a\x07\x00') or file_start.startswith(b'Rar!\x1a\x07\x01\x00'):
                    self.extract_rar_with_winrar(archive_path, app_dir)
                else:
                    raise Exception("Unsupported archive format (not ZIP or RAR)")

                messagebox.showinfo("Update Complete", "The app was updated and will now restart.")

                python = sys.executable
                os.execl(python, python, *sys.argv)

            except Exception as e:
                messagebox.showerror("Update Failed", f"Failed to update the app:\n{e}")
                
    def set_widgets_state(self, parent, state):
        for child in parent.winfo_children():
            try:
                child.configure(state=state)
            except Exception:
                pass  # Some widgets don't support state change
            # Recursively disable child widgets' children too
            self.set_widgets_state(child, state) 
    def set_loading_state(self, loading):
        state = 'disabled' if loading else 'normal'
        # Disable/enable search and sort widgets
        self.search_entry.configure(state=state)
        self.sort_menu.configure(state=state)
        # Disable/enable all mod widgets inside the available mods frame
        self.set_widgets_state(self.available_mods_frame, state)            
                       
    def setup_ui(self):
       
        self.notebook = ttk.Notebook(self.app)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        self.loading_label = ttk.Label(self.app, text="Initializing, please wait...", font=("Segoe UI", 12))
        self.spinner = ttk.Progressbar(self.app, mode='indeterminate',bootstyle="dark", length=200)
        self.spinner.pack()
        self.spinner.start()
        self.loading_label.pack(pady=20)

        self.available_tab = ttk.Frame(self.notebook)
        self.installed_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.available_tab, text="Available Mods")
        self.notebook.add(self.installed_tab, text="Installed Mods")
        self.notebook.add(self.settings_tab, text="Settings")


        # Available Mods Tab
        self.search_frame = ttk.Frame(self.available_tab)
        self.search_frame.pack(fill='x', padx=12, pady=10)

        self.search_entry = ttk.Entry(self.search_frame, textvariable=self.search_var, font=('TkDefaultFont', 11))
        self.search_entry.pack(side='left', fill='x', expand=True, padx=(0,8))
        self.search_entry.insert(0, "Search mods...")
        self.search_entry.config(foreground="gray")
        self.search_entry.bind("<FocusIn>", self.on_search_entry_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_search_entry_focus_out)
        self.search_var.trace_add("write", self.on_search_text_change)

        self.sort_menu = ttk.Combobox(self.search_frame, textvariable=self.sort_option, values=["Name", "Version"], width=12, state="readonly")
        self.sort_menu.pack(side='right')
        self.sort_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_available_tab(self.available_mods))

        canvas_container = ttk.Frame(self.available_tab)
        canvas_container.pack(fill='both', expand=True, padx=12, pady=10)

        self.available_canvas = tk.Canvas(canvas_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.available_canvas.yview)
        self.available_mods_frame = ttk.Frame(self.available_canvas)

        self.available_mods_frame.bind(
            "<Configure>",
            lambda e: self.available_canvas.configure(
                scrollregion=self.available_canvas.bbox("all")
            )
        )

        self.available_canvas.create_window((0, 0), window=self.available_mods_frame, anchor="nw")
        self.available_canvas.configure(yscrollcommand=scrollbar.set)
        self.set_loading_state(True)
        self.available_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Optional: enable mousewheel scrolling
        def _on_mousewheel(event):
            self.available_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.available_canvas.bind_all("<MouseWheel>", _on_mousewheel)




        # Installed Mods Tab
        self.installed_mods_frame = ttk.Frame(self.installed_tab)
        self.installed_mods_frame.pack(fill='both', expand=True, padx=12, pady=10)

        # Settings Tab
        ttk.Label(self.settings_tab, text="IOsoccer Game Path:", font=('TkDefaultFont', 12)).pack(pady=(20, 8))
        path_frame = ttk.Frame(self.settings_tab)
        path_frame.pack(pady=0, padx=10, fill='x')

        self.game_path_entry = ttk.Entry(path_frame, textvariable=self.game_path_var)
        self.game_path_entry.pack(side='left', fill='x', expand=True)
        self.game_path_entry.config(font=('TkDefaultFont', 11))

        browse_btn = ttk.Button(path_frame, text="Browse...", bootstyle="secondary-outline", command=self.browse_path)
        browse_btn.pack(side='left', padx=8)

        load_btn = ttk.Button(self.settings_tab, text="Reload Available Mods", bootstyle="info-outline", command=lambda: self.load_available_mods(force=True))
        load_btn.pack(pady=20)
        ttk.Label(self.settings_tab, text="Made with love by SyRoX <3", font=('TkDefaultFont', 10), foreground="gray").pack(pady=(0,20))


## Load config.json
    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.game_path_var.set(data.get("game_path", ""))
                    # Load only mod names as a list of strings
                    self.installed_mod_names = data.get("installed_mods", [])
                    # Initialize installed_mods as empty for now — full info will come later
                    self.installed_mods = []
            except Exception as e:
                print(f"Failed to load config: {e}")
                self.installed_mod_names = []
                self.installed_mods = []
                self.game_path_var.set("")
        else:
            self.installed_mod_names = []
            self.installed_mods = []
            self.game_path_var.set("")


            
            
    def save_config(self):
        # Extract only mod names from the installed_mods list of dicts
        installed_mod_names = [mod['name'] for mod in self.installed_mods] if hasattr(self, 'installed_mods') else []

        data = {
            "game_path": self.game_path_var.get(),
            "installed_mods": installed_mod_names
        }
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")  # Optional: debug print
        
        
    # UI Callbacks
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.game_path_var.set(path)
            self.save_config()

    def on_search_entry_focus_in(self, event):
        if self.search_entry.get() == "Search mods...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(foreground="white")

    def on_search_entry_focus_out(self, event):
        if self.search_entry.get().strip() == "":
            self.search_entry.insert(0, "Search mods...")
            self.search_entry.config(foreground="gray")

    def on_search_text_change(self, *args):
        if not self.search_loaded:
            return
        self.refresh_available_tab(self.available_mods)

    # Image loading

    def load_image_from_url(self, url, size=(128, 72)):
        try:
            if url in self.thumbnails:
                return self.thumbnails[url]

            # Unique filename for caching
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = os.path.join(self.cache_dir, f"{url_hash}.png")

            # Use cache if file exists
            if os.path.exists(cache_path):
                image = Image.open(cache_path).convert("RGBA")
            else:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, timeout=4, headers=headers)
                response.raise_for_status()
                img_data = response.content
                image = Image.open(BytesIO(img_data)).convert("RGBA")
                image.save(cache_path)  # Save to cache

            image = image.resize(size, Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(image)
            self.thumbnails[url] = tk_img
            return tk_img
        except Exception as e:
            print(f"Image load failed for {url}: {e}")
            return self.placeholder_img
    def load_image_async(self, url, label, size=(128, 72)):
        def _load():
            img = self.load_image_from_url(url, size)
            if img:
                self.app.after(0, lambda: label.config(image=img))
                self.app.after(0, lambda: setattr(label, 'image', img))
        threading.Thread(target=_load, daemon=True).start()


    # Refresh UI
    def refresh_available_tab(self, mods):
        for widget in self.available_mods_frame.winfo_children():
            widget.destroy()
        
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            self.spinner.stop()
            self.spinner.pack_forget()
        
        query = self.search_var.get().strip()
        filtered = mods
        if query and query.lower() != "search mods...":
            filtered = [m for m in mods if query.lower() in m['name'].lower()]

        if self.sort_option.get() == "Name":
            filtered.sort(key=lambda m: m['name'].lower())
        elif self.sort_option.get() == "Version":
            filtered.sort(key=lambda m: m['version'], reverse=True)

        if not filtered:
            ttk.Label(self.available_mods_frame, text="No mods found.", font=('TkDefaultFont', 12, 'italic')).pack(pady=20)
            return

        for mod in filtered:
            frame = ttk.Frame(self.available_mods_frame, padding=8, style="Card.TFrame")
            frame.pack(fill='x', padx=12, pady=6)

            img_label = ttk.Label(frame)
            img_label.pack(side='left', padx=5)

            img_url = mod.get('image_url') or mod.get('thumbnail') or ''
            img_label.config(image=self.placeholder_img)
            img_label.image = self.placeholder_img
            self.load_image_async(img_url, img_label)


            info_frame = ttk.Frame(frame)
            info_frame.pack(side='left', fill='x', expand=True, padx=10)

            ttk.Label(info_frame, text=mod['name'], font=('TkDefaultFont', 13, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Version: {mod['version']}", bootstyle="secondary").pack(anchor='w')
            ttk.Label(info_frame, text=mod.get('description', ''), wraplength=600).pack(anchor='w', pady=(4,6))

            # Click to show details
            frame.bind("<Button-1>", lambda e, m=mod: self.show_mod_details(m))
            for child in frame.winfo_children():
                child.bind("<Button-1>", lambda e, m=mod: self.show_mod_details(m))
        self.set_loading_state(False)
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            self.spinner.stop()
            self.spinner.pack_forget()


    def finish_loading(self):
        self.load_available_mods()
        self.check_for_updates()
    
    def rebuild_installed_mods_from_names(self):
        if hasattr(self, 'installed_mod_names'):
            self.installed_mods = [mod for mod in self.available_mods if mod['name'] in self.installed_mod_names]
        else:
            self.installed_mods = []
        self.refresh_installed_tab()
        
    def show_mod_details(self, mod):
        detail_win = tb.Toplevel(self.app)
        detail_win.title(mod['name'])
        detail_win.geometry("700x550")
        detail_win.configure(bg="#222222")

        

        
        desc = mod.get('description', 'No description available.')
        ttk.Label(detail_win, text=desc, wraplength=650).pack(pady=5)

        info_frame = ttk.Frame(detail_win)
        info_frame.pack(pady=5, fill='x', padx=20)

        author = mod.get('author', 'Unknown Author')
        ttk.Label(info_frame, text=f"Author: {author}", font=('TkDefaultFont', 11, 'italic')).pack(anchor='w')
        version = mod.get('version', 'Unknown')
        ttk.Label(info_frame, text=f"Version: {version}", font=('TkDefaultFont', 11, 'italic')).pack(anchor='w')
        tags = mod.get('tags', [])
        if tags:
            tags_str = ", ".join(tags)
            ttk.Label(info_frame, text=f"Tags: {tags_str}", font=('TkDefaultFont', 11, 'italic')).pack(anchor='w')

        gallery_frame = ttk.Frame(detail_win)
        gallery_frame.pack(pady=8, fill='x', padx=20)

        images = mod.get('gallery', [])
        if not images:
            ttk.Label(gallery_frame, text="No gallery images available.", foreground="gray").pack()
        else:
            for url in images:
                img = self.load_image_from_url(url, size=(120, 120))
                if img:
                    lbl = ttk.Label(gallery_frame, image=img)
                    lbl.image = img
                    lbl.pack(side='left', padx=4)
        if mod.get('gallery') and len(mod['gallery']) > 0:
            print(f"Mod '{mod['name']}' has gallery images")
        else:
            print(f"Mod '{mod['name']}' has no gallery images")


        # Progress bar (hidden initially)
        progress_bar = ttk.Progressbar(detail_win, mode='indeterminate')
        
        
        self.spinner.pack()
        self.spinner.start()

        install_btn = ttk.Button(detail_win, text="Install Mod", bootstyle="success")
        install_btn.pack(pady=15)

        def on_install_click():
            progress_bar.pack(fill='x', padx=20, pady=(0,10))
            progress_bar.start()
            install_btn.config(state='disabled')
            self.install_mod(mod, detail_win, progress_bar)

        install_btn.config(command=on_install_click)
   
                # Load mods index from GitHub
    def load_available_mods(self, force=False):
            self.set_loading_state(True)
            def _load():
                try:
                    resp = requests.get(self.MOD_INDEX_URL, timeout=12)
                    resp.raise_for_status()
                    mod_urls = resp.json()  # This is a list of URLs

                    mods = []
                    for url in mod_urls:
                        try:
                            r = requests.get(url, timeout=10)
                            r.raise_for_status()
                            mod = r.json()
                            mods.append(mod)
                        except Exception as e:
                            print(f"Failed to load mod from {url}: {e}")

                    self.available_mods = mods
                    self.search_loaded = True
                    self.app.after(0, lambda: self.refresh_available_tab(mods))
                    self.rebuild_installed_mods_from_names()

                except Exception as e:
                    self.app.after(0, lambda: messagebox.showerror("Error", f"Failed to load mod list:\n{str(e)}"))

            threading.Thread(target=_load, daemon=True).start()


    # Installed mods UI refresh
    def refresh_installed_tab(self):
        for widget in self.installed_mods_frame.winfo_children():
            widget.destroy()

        if not self.installed_mods:
            ttk.Label(self.installed_mods_frame, text="No mods installed.", font=('TkDefaultFont', 12, 'italic')).pack(pady=20)
            return

        # Sort installed mods if dropdown exists
        if hasattr(self, "installed_sort_var"):
            sort_key = self.installed_sort_var.get()
            mods = self.installed_mods.copy()
            if sort_key == "Name":
                mods.sort(key=lambda m: m['name'].lower())
            elif sort_key == "Version":
                mods.sort(key=lambda m: m.get('version', ''), reverse=True)
            elif sort_key == "Install Date":
                mods.sort(key=lambda m: m.get('installed_at', ''), reverse=True)
        else:
            mods = self.installed_mods

        for mod in mods:
            frame = ttk.Frame(self.installed_mods_frame, padding=8, style="Card.TFrame")
            frame.pack(fill='x', padx=12, pady=6)

            # Thumbnail
            thumb_label = ttk.Label(frame)
            thumb_label.pack(side='left', padx=(0, 10))
            thumb_label.config(image=self.placeholder_img)
            thumb_label.image = self.placeholder_img
            self.load_image_async(mod.get("image_url") or mod.get("thumbnail") or "", thumb_label, size=(72, 72))

            # Mod info
            info_frame = ttk.Frame(frame)
            info_frame.pack(side='left', fill='both', expand=True)

            ttk.Label(info_frame, text=mod['name'], font=('TkDefaultFont', 13, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=f"Version: {mod.get('version', 'Unknown')}", bootstyle="secondary").pack(anchor='w')

            installed_at = mod.get('installed_at', None)
            if installed_at:
                ttk.Label(info_frame, text=f"Installed: {installed_at}", font=('TkDefaultFont', 9, 'italic'), foreground="gray").pack(anchor='w')

            desc = mod.get('description', '')
            if desc:
                ttk.Label(info_frame, text=desc[:100] + "..." if len(desc) > 100 else desc, wraplength=400).pack(anchor='w', pady=(4, 0))

            # Action buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side='right', padx=8)

            ttk.Button(btn_frame, text="Uninstall", bootstyle="danger", command=lambda m=mod: self.uninstall_mod(m)).pack(pady=2)


    # Helper: Find WinRAR executable on Windows
    def find_winrar_path(self):
        if platform.system() != "Windows":
            return None
        possible_paths = [
            r"C:\Program Files\WinRAR\WinRAR.exe",
            r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
        ]
        for path in possible_paths:
            if os.path.isfile(path):
                return path
        return None

    # Helper: Ask user to locate WinRAR.exe if not found
    def browse_for_winrar(self):
        messagebox.showinfo("Locate WinRAR", "Please locate your WinRAR.exe")
        path = filedialog.askopenfilename(
            title="Locate WinRAR.exe",
            filetypes=[("WinRAR executable", "WinRAR.exe")],
        )
        if path and os.path.isfile(path):
            return path
        return None
# If can't find, user have to download it by himself !

    # Helper: Extract RAR archive with WinRAR CLI
    def extract_rar_with_winrar(self, rar_path, dest_path, winrar_path=None):
        if not winrar_path:
            winrar_path = self.find_winrar_path()
        if not winrar_path:
            winrar_path = self.browse_for_winrar()
        if not winrar_path:
            raise FileNotFoundError("WinRAR executable not found.")

        cmd = [winrar_path, "x", "-y", rar_path, dest_path]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"WinRAR extraction failed: {e.stderr.decode()}")

    # Install mod with archive download and extraction (ZIP or RAR with WinRAR fallback)
    def install_mod(self, mod, window=None, progress_bar=None):
            game_path = self.game_path_var.get().strip()
            if not game_path or not os.path.isdir(game_path):
                messagebox.showerror("Error", "Invalid IOsoccer game path. Please set it correctly in Settings.")
                if progress_bar:
                    self.app.after(0, lambda: progress_bar.stop())
                    self.app.after(0, lambda: progress_bar.pack_forget())
                return

            download_url = mod.get('download_url')
            if not download_url:
                messagebox.showerror("Error", "Mod download URL is missing.")
                if progress_bar:
                    self.app.after(0, lambda: progress_bar.stop())
                    self.app.after(0, lambda: progress_bar.pack_forget())
                return

            def do_install():
                try:
                    temp_dir = tempfile.mkdtemp(prefix="iosoccer_mod_")
                    archive_path = os.path.join(temp_dir, "mod_archive")

                    # Download archive
                    with requests.get(download_url, stream=True, timeout=20) as r:
                        r.raise_for_status()
                        with open(archive_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)

                    # Detect archive type
                    with open(archive_path, "rb") as f:
                        file_start = f.read(8)

                    if file_start.startswith(b'PK'):
                        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                            zip_ref.extractall(game_path)
                    elif file_start.startswith(b'Rar!\x1a\x07\x00') or file_start.startswith(b'Rar!\x1a\x07\x01\x00'):
                        try:
                            import rarfile
                            with rarfile.RarFile(archive_path) as rar_ref:
                                rar_ref.extractall(game_path)
                        except (ImportError, Exception):
                            self.extract_rar_with_winrar(archive_path, game_path)
                    else:
                        raise Exception("Unsupported archive format (not ZIP or RAR)")

                    # Rename 'backup' folder to '{modname}.backup'
                    backup_folder = os.path.join(game_path, "backup")
                    new_backup_folder = os.path.join(game_path, f"{mod['name']}.backup")
                    if os.path.isdir(backup_folder):
                        try:    
                            if os.path.exists(new_backup_folder):
                                shutil.rmtree(new_backup_folder)
                            os.rename(backup_folder, new_backup_folder)
                        except Exception as e:
                            print(f"Failed to rename backup folder: {e}")

                    shutil.rmtree(temp_dir)

                    self.installed_mods.append(mod)
                    self.refresh_installed_tab()

                    if progress_bar:
                        self.app.after(0, lambda: progress_bar.stop())
                        self.app.after(0, lambda: progress_bar.pack_forget())

                    self.app.after(0, lambda: messagebox.showinfo("Success", f"Installed mod '{mod['name']}' successfully!"))
                    if mod['name'] not in self.installed_mod_names:
                        self.installed_mod_names.append(mod['name'])
                        self.installed_mods = [m for m in self.available_mods if m['name'] in self.installed_mod_names]
                        self.save_config()
                        self.app.after(0, self.refresh_installed_tab)
                    if window:
                        window.destroy()
                    if mod not in self.installed_mods:
                        self.installed_mods.append(mod)
                        self.save_installed_mods()  
                except Exception as e:
                    if progress_bar:
                        self.app.after(0, lambda: progress_bar.stop())
                        self.app.after(0, lambda: progress_bar.pack_forget())
                    self.app.after(0, lambda e=e: messagebox.showerror("Error", f"Failed to install mod:\n{str(e)}"))

            threading.Thread(target=do_install, daemon=True).start()



    def uninstall_mod(self, mod):
        game_path = self.game_path_var.get().strip()
        if not game_path or not os.path.isdir(game_path):
            messagebox.showerror("Error", "Invalid IOsoccer game path. Please set it correctly in Settings.")
            return

        confirm = messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall mod '{mod['name']}'?")
        if not confirm:
            return

        backup_path = os.path.join(game_path, f"{mod['name']}.backup")
        if not os.path.exists(backup_path):
            messagebox.showwarning("Backup Not Found", f"No backup folder found for mod '{mod['name']}'. Uninstall might be incomplete.")
        else:
            try:
                # Restore files from backup by copying and overwriting
                for root, dirs, files in os.walk(backup_path):
                    rel_path = os.path.relpath(root, backup_path)
                    dest_dir = os.path.join(game_path, rel_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)

                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        shutil.copy2(src_file, dest_file)

                # Delete backup folder after restoration
                shutil.rmtree(backup_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore backup files:\n{str(e)}")
                return

        try:
            # Remove the mod name from installed_mod_names list
            if mod['name'] in self.installed_mod_names:
                self.installed_mod_names.remove(mod['name'])

            # Rebuild installed_mods list from names to keep full info consistent
            self.installed_mods = [m for m in self.available_mods if m['name'] in self.installed_mod_names]

            # Save config to persist changes
            self.save_config()

            # Refresh UI
            self.refresh_installed_tab()

            messagebox.showinfo("Uninstalled", f"Mod '{mod['name']}' uninstalled successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update installed mods list:\n{str(e)}")

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    app = ModManagerApp()
    app.run()
