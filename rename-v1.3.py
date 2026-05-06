import os
import random
import string
import datetime
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from PIL import Image
from PIL.ExifTags import TAGS
import re

try:
    import exifread
    EXIFREAD_AVAILABLE = True
    EXIFREAD_VERSION = getattr(exifread, '__version__', 'unknown')
except ImportError:
    EXIFREAD_AVAILABLE = False
    EXIFREAD_VERSION = None

# ======================== 用户配置区域 ========================
DEFAULT_SOURCE_FOLDER = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PREFIX = "screenshot"
DEFAULT_TEMPLATE = "{filetype}{prefix}-{YYYY}-{MM}-{DD}-{hh}{mm}-{id}"
DEFAULT_RECURSIVE = False
DEFAULT_COPY_TO_NEW = True
DEFAULT_VERBOSE_LOG = False
DEFAULT_IMAGE_CHECKED = True
DEFAULT_RAW_CHECKED = False
DEFAULT_DIGITAL_CHECKED = False
DEFAULT_VIDEO_CHECKED = True
DEFAULT_AUDIO_CHECKED = False
# ============================================================

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("多媒体文件批量重命名工具 V1.3")
        self.root.geometry("920x720")

        self.folder_path = tk.StringVar(value=DEFAULT_SOURCE_FOLDER)
        self.prefix = tk.StringVar(value=DEFAULT_PREFIX)
        self.template = tk.StringVar(value=DEFAULT_TEMPLATE)
        self.recursive = tk.BooleanVar(value=DEFAULT_RECURSIVE)
        self.copy_to_new = tk.BooleanVar(value=DEFAULT_COPY_TO_NEW)
        self.verbose_log = tk.BooleanVar(value=DEFAULT_VERBOSE_LOG)
        self.target_folder = tk.StringVar()

        self.categories = {
            'image': tk.BooleanVar(value=DEFAULT_IMAGE_CHECKED),
            'raw': tk.BooleanVar(value=DEFAULT_RAW_CHECKED),
            'digital': tk.BooleanVar(value=DEFAULT_DIGITAL_CHECKED),
            'video': tk.BooleanVar(value=DEFAULT_VIDEO_CHECKED),
            'audio': tk.BooleanVar(value=DEFAULT_AUDIO_CHECKED),
        }

        self.image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        self.raw_exts = ('.arw', '.cr2', '.cr3', '.dng', '.nef', '.nrw',
                         '.orf', '.pef', '.raf', '.rw2', '.srw', '.x3f')
        self.digital_image_exts = ('.tiff', '.tif')
        self.video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',
                           '.m4v', '.mpg', '.mpeg')
        self.audio_exts = ('.mp3', '.wav', '.flac', '.aac', '.ogg',
                           '.m4a', '.wma')

        self.create_widgets()
        self.template.trace_add("write", lambda *args: self.update_preview())
        self.prefix.trace_add("write", lambda *args: self.update_preview())
        self.update_preview()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def create_widgets(self):
        # 源文件夹
        f1 = tk.Frame(self.root)
        f1.pack(pady=5, fill=tk.X, padx=5)
        tk.Label(f1, text="源文件夹：").pack(side=tk.LEFT)
        tk.Entry(f1, textvariable=self.folder_path).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        tk.Button(f1, text="浏览", command=self.select_folder).pack(side=tk.LEFT)

        # 复制到新目录
        f2 = tk.Frame(self.root)
        f2.pack(pady=5, fill=tk.X, padx=5)
        self.copy_check = tk.Checkbutton(f2, text="复制到新目录（保护原文件）",
                                         variable=self.copy_to_new, command=self.toggle_target_folder)
        self.copy_check.pack(side=tk.LEFT)
        self.target_entry = tk.Entry(f2, textvariable=self.target_folder, state='disabled')
        self.target_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.target_button = tk.Button(f2, text="浏览", command=self.select_target_folder, state='disabled')
        self.target_button.pack(side=tk.LEFT)

        # 前缀
        f3 = tk.Frame(self.root)
        f3.pack(pady=5, fill=tk.X, padx=5)
        tk.Label(f3, text="自定义前缀：").pack(side=tk.LEFT)
        tk.Entry(f3, textvariable=self.prefix, width=30).pack(side=tk.LEFT, padx=5)
        tk.Label(f3, text="(用于模板中的 {prefix})").pack(side=tk.LEFT)

        # 递归
        f4 = tk.Frame(self.root)
        f4.pack(pady=5, fill=tk.X, padx=5)
        tk.Checkbutton(f4, text="包含子文件夹", variable=self.recursive).pack(side=tk.LEFT)

        # 详细日志
        f5 = tk.Frame(self.root)
        f5.pack(pady=5, fill=tk.X, padx=5)
        tk.Checkbutton(f5, text="详细日志模式", variable=self.verbose_log).pack(side=tk.LEFT)

        # 文件类型
        f6 = tk.LabelFrame(self.root, text="处理类型", padx=5, pady=5)
        f6.pack(pady=5, fill=tk.X, padx=5)
        tk.Checkbutton(f6, text="图像类 (.jpg .jpeg .png .bmp .gif .webp)",
                       variable=self.categories['image'], anchor='w').pack(fill=tk.X)
        tk.Checkbutton(f6, text=f"RAW类 {' '.join(self.raw_exts)}",
                       variable=self.categories['raw'], anchor='w').pack(fill=tk.X)
        tk.Checkbutton(f6, text=f"数字图像类 {' '.join(self.digital_image_exts)}",
                       variable=self.categories['digital'], anchor='w').pack(fill=tk.X)
        tk.Checkbutton(f6, text=f"视频类 {' '.join(self.video_exts)}",
                       variable=self.categories['video'], anchor='w').pack(fill=tk.X)
        tk.Checkbutton(f6, text=f"音频类 {' '.join(self.audio_exts)}",
                       variable=self.categories['audio'], anchor='w').pack(fill=tk.X)

        # 文件名模板
        f7 = tk.Frame(self.root)
        f7.pack(pady=5, fill=tk.X, padx=5)
        tk.Label(f7, text="文件名模板：").pack(side=tk.LEFT)
        tk.Entry(f7, textvariable=self.template, width=50).pack(side=tk.LEFT, padx=5)

        # 占位符说明（只读输入框）
        help_line1 = ("可用占位符：{YYYY}(四位年)  {YY}(两位年)  {MM}(月)  {DD}(日)  "
                      "{hh}(时)  {mm}(分)  {ss}(秒)  {prefix}(自定义前缀)  {id}(4位标识码)  "
                      "{filetype}(文件类别: IMAGE/RAW/DIGITAL/VIDEO/AUDIO)")
        help_line2 = "示例模板: {prefix}-{YYYY}-{MM}-{DD}-{hh}{mm}-{id}  或  {filetype}{prefix}-{YYYY}{MM}{DD}-{id}"

        self.help_var1 = tk.StringVar(value=help_line1)
        self.help_entry1 = tk.Entry(self.root, textvariable=self.help_var1,
                                    state='readonly', fg='blue', font=("TkDefaultFont", 9),
                                    readonlybackground=self.root.cget("bg"),
                                    relief='flat', borderwidth=0)
        self.help_entry1.pack(pady=(2,0), padx=5, fill=tk.X)

        self.help_var2 = tk.StringVar(value=help_line2)
        self.help_entry2 = tk.Entry(self.root, textvariable=self.help_var2,
                                    state='readonly', fg='blue', font=("TkDefaultFont", 9),
                                    readonlybackground=self.root.cget("bg"),
                                    relief='flat', borderwidth=0)
        self.help_entry2.pack(pady=(0,2), padx=5, fill=tk.X)

        # EXIF 库状态
        exif_status = (f"✓ 使用 ExifRead {EXIFREAD_VERSION} (支持RAW/HEIC等)"
                       if EXIFREAD_AVAILABLE else "⚠ 使用 PIL (基础EXIF支持，建议安装exifread)")
        tk.Label(self.root, text=exif_status, fg="purple").pack(pady=2)

        # 文件名预览（只读输入框）
        self.preview_var = tk.StringVar()
        self.preview_entry = tk.Entry(self.root, textvariable=self.preview_var,
                                      state='readonly', fg='green', font=("TkDefaultFont", 9),
                                      readonlybackground=self.root.cget("bg"),
                                      relief='flat', borderwidth=0)
        self.preview_entry.pack(pady=5, padx=5, fill=tk.X)

        # 开始按钮
        tk.Button(self.root, text="开始重命名", command=self.start_rename,
                  bg="#4CAF50", fg="white").pack(pady=10)

        # 日志区
        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=14, state='normal')
        self.log_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.toggle_target_folder()

    def toggle_target_folder(self):
        if self.copy_to_new.get():
            self.target_entry.config(state='normal')
            self.target_button.config(state='normal')
        else:
            self.target_entry.config(state='disabled')
            self.target_button.config(state='disabled')

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def select_target_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder.set(folder)

    def log(self, message, level="INFO"):
        self.log_area.insert(tk.END, f"[{level}] {message}\n")
        self.log_area.see(tk.END)
        self.root.update()

    def update_preview(self):
        template = self.template.get().strip()
        prefix = self.prefix.get().strip()
        example_dt = datetime.datetime(2026, 3, 13, 14, 30, 45)
        example_name = self.apply_template(template, example_dt, prefix, "ABCD", "IMAGE")
        self.preview_var.set(f"示例：{example_name}.jpg")

    def get_filetype(self, ext):
        if ext in self.image_exts:
            return "IMAGE"
        if ext in self.raw_exts:
            return "RAW"
        if ext in self.digital_image_exts:
            return "DIGITAL"
        if ext in self.video_exts:
            return "VIDEO"
        if ext in self.audio_exts:
            return "AUDIO"
        return ""

    def parse_date_string(self, date_str):
        date_str = str(date_str).strip()
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        date_str = date_str.replace('T', ' ')
        formats = [
            "%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
            "%Y:%m:%d %H:%M", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M",
            "%Y:%m:%d", "%Y-%m-%d", "%Y/%m/%d",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M",
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期字符串: {date_str}")

    def parse_xmp_content(self, xmp_str):
        patterns = [
            r'xmp:CreateDate="([^"]+)"', r'xmp:DateCreated="([^"]+)"',
            r'xmp:MetadataDate="([^"]+)"',
            r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>',
            r'<xmp:DateCreated>([^<]+)</xmp:DateCreated>',
            r'<xmp:MetadataDate>([^<]+)</xmp:MetadataDate>',
            r'photoshop:DateCreated="([^"]+)"',
            r'<photoshop:DateCreated>([^<]+)</photoshop:DateCreated>',
        ]
        for pat in patterns:
            m = re.search(pat, xmp_str)
            if m:
                try:
                    return self.parse_date_string(m.group(1).strip())
                except ValueError:
                    continue
        return None

    def parse_xmp_sidecar(self, filepath):
        xmp_path = os.path.splitext(filepath)[0] + '.xmp'
        if os.path.exists(xmp_path):
            self.log(f"找到XMP侧边文件: {xmp_path}")
            try:
                with open(xmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    xmp_str = f.read()
                if self.verbose_log.get():
                    self.log(f"[XMP] 前200字符: {xmp_str[:200]}", "DEBUG")
                dt = self.parse_xmp_content(xmp_str)
                if dt:
                    self.log(f"[XMP] 解析到日期 {dt}")
                    return dt
            except Exception as e:
                self.log(f"[XMP] 读取失败: {e}", "WARNING")
        return None

    def get_media_datetime(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if not (ext in self.image_exts or ext in self.raw_exts or ext in self.digital_image_exts):
            mtime = os.path.getmtime(filepath)
            dt = datetime.datetime.fromtimestamp(mtime)
            self.log(f"非图像文件，使用修改时间")
            return dt, True, "File Modification Time (non-image)"

        date_tags = [
            ('EXIF DateTimeOriginal', 'DateTimeOriginal'),
            ('Image DateTime', 'Image DateTime'),
            ('EXIF DateTimeDigitized', 'DateTimeDigitized'),
            ('EXIF DateTime', 'EXIF DateTime'),
            ('EXIF_DateTimeOriginal', 'EXIF_DateTimeOriginal'),
            ('Image_DateTime', 'Image_DateTime'),
        ]

        if EXIFREAD_AVAILABLE:
            try:
                with open(filepath, 'rb') as f:
                    tags = exifread.process_file(f, details=True)
                if self.verbose_log.get():
                    self.log(f"[ExifRead] 标签数: {len(tags)}", "DEBUG")
                for tag_key, reason in date_tags:
                    if tag_key in tags:
                        dt_str = str(tags[tag_key])
                        try:
                            dt = self.parse_date_string(dt_str)
                            is_fallback = ('Original' not in tag_key)
                            return dt, is_fallback, f"ExifRead: {tag_key}"
                        except ValueError:
                            continue
                for xmp_tag in ['Image XMP', 'Image XML', 'XMP', 'XML']:
                    if xmp_tag in tags:
                        dt = self.parse_xmp_content(str(tags[xmp_tag]))
                        if dt:
                            return dt, False, f"XMP from {xmp_tag}"
                dt = self.parse_xmp_sidecar(filepath)
                if dt:
                    return dt, False, "XMP sidecar file"
            except Exception as e:
                if self.verbose_log.get():
                    self.log(f"[ExifRead] 异常: {e}", "WARNING")

        try:
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                pil_tags = {TAGS.get(tid, str(tid)): val for tid, val in exif.items()}
                for tag_name, reason in [('DateTimeOriginal', 'DateTimeOriginal'),
                                         ('DateTime', 'DateTime'),
                                         ('DateTimeDigitized', 'DateTimeDigitized')]:
                    if tag_name in pil_tags:
                        dt_str = str(pil_tags[tag_name])
                        try:
                            dt = self.parse_date_string(dt_str)
                            is_fallback = (tag_name != 'DateTimeOriginal')
                            return dt, is_fallback, f"PIL: {tag_name}"
                        except ValueError:
                            continue
        except Exception as e:
            if self.verbose_log.get():
                self.log(f"[PIL] 异常: {e}", "ERROR")

        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt, True, "File Modification Time (fallback)"

    def generate_unique_id(self, existing_ids):
        chars = string.ascii_uppercase + string.digits
        while True:
            new_id = ''.join(random.choices(chars, k=4))
            if new_id not in existing_ids:
                return new_id

    def sanitize_filename(self, filename):
        for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            filename = filename.replace(ch, '_')
        return filename

    def apply_template(self, template, dt, prefix, file_id, filetype):
        r = {
            "{YYYY}": dt.strftime("%Y"),
            "{YY}": dt.strftime("%y"),
            "{MM}": dt.strftime("%m"),
            "{DD}": dt.strftime("%d"),
            "{hh}": dt.strftime("%H"),
            "{mm}": dt.strftime("%M"),
            "{ss}": dt.strftime("%S"),
            "{prefix}": prefix,
            "{id}": file_id,
            "{filetype}": filetype,
        }
        result = template
        for k, v in r.items():
            result = result.replace(k, v)
        return result

    def collect_all_files(self, folder, recursive):
        """收集所有文件，跳过无权限的目录"""
        all_files = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                try:
                    for f in files:
                        all_files.append(os.path.join(root, f))
                except PermissionError:
                    self.log(f"权限不足，跳过目录: {root}", "WARNING")
        else:
            try:
                for f in os.listdir(folder):
                    full = os.path.join(folder, f)
                    if os.path.isfile(full):
                        all_files.append(full)
            except PermissionError:
                self.log(f"权限不足，无法列出目录: {folder}", "WARNING")
        return all_files

    def collect_media_files(self, folder, recursive):
        """收集媒体文件，跳过无权限的目录"""
        media_files = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                try:
                    for file in files:
                        full_path = os.path.join(root, file)
                        ext = os.path.splitext(file)[1].lower()
                        if self._is_selected_category(ext):
                            media_files.append(full_path)
                except PermissionError:
                    self.log(f"权限不足，跳过目录: {root}", "WARNING")
        else:
            try:
                for file in os.listdir(folder):
                    full_path = os.path.join(folder, file)
                    if os.path.isfile(full_path):
                        ext = os.path.splitext(file)[1].lower()
                        if self._is_selected_category(ext):
                            media_files.append(full_path)
            except PermissionError:
                self.log(f"权限不足，无法列出目录: {folder}", "WARNING")
        return media_files

    def _is_selected_category(self, ext):
        if ext in self.image_exts:
            return self.categories['image'].get()
        if ext in self.raw_exts:
            return self.categories['raw'].get()
        if ext in self.digital_image_exts:
            return self.categories['digital'].get()
        if ext in self.video_exts:
            return self.categories['video'].get()
        if ext in self.audio_exts:
            return self.categories['audio'].get()
        return False

    def get_relative_path(self, full_path, base_folder):
        try:
            return os.path.relpath(os.path.dirname(full_path), base_folder)
        except ValueError:
            return os.path.dirname(full_path)

    def show_ignored_files_dialog(self, ignored_files, folder, total_files, ignored_count):
        dlg = tk.Toplevel(self.root)
        dlg.title("忽略文件列表")
        dlg.geometry("600x400")
        dlg.transient(self.root)
        dlg.grab_set()

        msg = f"当前目录下共有 {total_files} 个文件，其中 {ignored_count} 个不是支持的媒体格式，将不会被处理："
        tk.Label(dlg, text=msg, wraplength=550, justify=tk.LEFT).pack(pady=10, padx=10)

        frame = tk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(frame, yscrollcommand=sb.set, font=("Courier", 10))
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        for f in ignored_files:
            lb.insert(tk.END, f)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)
        ans = [False]

        def cont():
            ans[0] = True
            dlg.destroy()
        def canc():
            dlg.destroy()

        tk.Button(btn_frame, text="继续", command=cont, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=canc, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dlg)
        return ans[0]

    def show_rename_confirmation_dialog(self, rename_map, folder, target_base, copy_mode):
        dlg = tk.Toplevel(self.root)
        dlg.title("确认重命名")
        dlg.geometry("700x500")
        dlg.transient(self.root)
        dlg.grab_set()

        msg = f"将重命名以下 {len(rename_map)} 个文件："
        tk.Label(dlg, text=msg, wraplength=650, justify=tk.LEFT).pack(pady=10, padx=10)

        frame = tk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(frame, yscrollcommand=sb.set, font=("Courier", 9))
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        for old_path, new_path in rename_map:
            old_rel = os.path.relpath(old_path, folder)
            try:
                new_rel = os.path.relpath(new_path, target_base) if copy_mode else os.path.relpath(new_path, folder)
            except ValueError:
                new_rel = new_path
            lb.insert(tk.END, f"{old_rel} -> {new_rel}")

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)
        ans = [False]

        def conf():
            ans[0] = True
            dlg.destroy()
        def canc():
            dlg.destroy()

        tk.Button(btn_frame, text="确定", command=conf, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=canc, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dlg)
        return ans[0]

    def show_fallback_files_dialog(self, fallback_files, folder, previews_dict):
        dlg = tk.Toplevel(self.root)
        dlg.title("使用其他日期或修改时间的文件")
        dlg.geometry("700x400")
        dlg.transient(self.root)
        dlg.grab_set()

        msg = f"以下 {len(fallback_files)} 个文件未能使用原始拍摄时间，将使用其他日期或修改时间："
        tk.Label(dlg, text=msg, wraplength=650, justify=tk.LEFT).pack(pady=10, padx=10)

        frame = tk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sb = tk.Scrollbar(frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(frame, yscrollcommand=sb.set, font=("Courier", 9))
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=lb.yview)

        for f in fallback_files:
            old_name = os.path.basename(f)
            info = previews_dict.get(f, {})
            lb.insert(tk.END, f"{old_name} -> {info.get('preview', '?')}  [{info.get('reason', '?')}]")

        def on_dbl(event):
            sel = lb.curselection()
            if sel:
                path = fallback_files[sel[0]]
                if os.name == 'nt':
                    os.startfile(os.path.dirname(path))
                else:
                    import subprocess
                    try:
                        subprocess.Popen(['xdg-open', os.path.dirname(path)])
                    except Exception:
                        pass

        lb.bind("<Double-Button-1>", on_dbl)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(pady=10)
        ans = [False]

        def cont():
            ans[0] = True
            dlg.destroy()
        def canc():
            dlg.destroy()

        tk.Button(btn_frame, text="继续", command=cont, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=canc, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dlg)
        return ans[0]

    def start_rename(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择一个有效的源文件夹")
            return

        copy_mode = self.copy_to_new.get()
        target_base = None
        if copy_mode:
            target_base = self.target_folder.get().strip()
            if not target_base:
                messagebox.showerror("错误", "请选择一个目标文件夹")
                return
            os.makedirs(target_base, exist_ok=True)

        self.log_area.delete(1.0, tk.END)
        self.log(f"使用 EXIF 库: {'ExifRead' if EXIFREAD_AVAILABLE else 'PIL'}")

        all_files = self.collect_all_files(folder, self.recursive.get())
        total_files = len(all_files)
        media_files = self.collect_media_files(folder, self.recursive.get())
        media_count = len(media_files)
        ignored_count = total_files - media_count

        if ignored_count > 0:
            ignored_list = sorted(set(all_files) - set(media_files))
            rel_ignored = [os.path.relpath(f, folder) for f in ignored_list]
            if not self.show_ignored_files_dialog(rel_ignored, folder, total_files, ignored_count):
                self.log("用户取消重命名")
                return
            self.log(f"忽略非媒体文件 {ignored_count} 个")

        if not media_files:
            self.log("没有找到可处理的媒体文件", "WARNING")
            return

        self.log(f"找到 {media_count} 个媒体文件，开始分析...")
        if copy_mode:
            self.log(f"将复制到目标文件夹：{target_base}")

        template = self.template.get().strip()
        if not template:
            messagebox.showerror("错误", "文件名模板不能为空")
            return
        prefix = self.prefix.get().strip()

        cache_media_info = {}
        fallback_files = []
        fallback_previews = {}
        for filepath in media_files:
            self.log(f"{'─'*20} 处理文件: {os.path.basename(filepath)} {'─'*20}")
            original_mtime = os.path.getmtime(filepath)
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.jpeg':
                ext = '.jpg'
            dt, is_fallback, reason = self.get_media_datetime(filepath)
            filetype = self.get_filetype(ext)
            cache_media_info[filepath] = (dt, ext, filetype, is_fallback, reason, original_mtime)
            if is_fallback:
                fallback_files.append(filepath)
                pname = self.apply_template(template, dt, prefix, "XXXX", filetype)
                pname = self.sanitize_filename(pname) + ext
                fallback_previews[filepath] = {'preview': pname, 'reason': reason}

        if fallback_files:
            if not self.show_fallback_files_dialog(fallback_files, folder, fallback_previews):
                self.log("用户取消重命名")
                return
            self.log(f"有 {len(fallback_files)} 个文件使用其他日期或修改时间")

        existing_ids = set()
        rename_map = []
        failed_list = []

        for filepath in media_files:
            self.log(f"{'─'*20} 重命名映射: {os.path.basename(filepath)} {'─'*20}")
            dt, ext, filetype, _, _, original_mtime = cache_media_info[filepath]

            if not os.path.exists(filepath):
                self.log("文件已不存在，跳过", "WARNING")
                failed_list.append(filepath)
                continue
            if os.path.getmtime(filepath) != original_mtime:
                self.log("文件已被修改，跳过以保证数据一致", "WARNING")
                failed_list.append(filepath)
                continue

            new_id = self.generate_unique_id(existing_ids)
            existing_ids.add(new_id)
            base_name = self.apply_template(template, dt, prefix, new_id, filetype)
            base_name = self.sanitize_filename(base_name)
            new_filename = base_name + ext

            if copy_mode:
                rel_dir = self.get_relative_path(filepath, folder)
                target_dir = os.path.join(target_base, rel_dir) if rel_dir not in (".", "") else target_base
                os.makedirs(target_dir, exist_ok=True)
                new_path = os.path.join(target_dir, new_filename)
            else:
                dir_name = os.path.dirname(filepath)
                new_path = os.path.join(dir_name, new_filename)
                if new_path == filepath:
                    self.log("无需重命名")
                    continue

            if len(new_path) > 259:
                self.log(f"新路径过长 ({len(new_path)} 字符)，跳过", "WARNING")
                continue

            attempt = 0
            path_too_long = False
            while os.path.exists(new_path) and attempt < 10:
                new_id = self.generate_unique_id(existing_ids)
                existing_ids.add(new_id)
                base_name = self.apply_template(template, dt, prefix, new_id, filetype)
                base_name = self.sanitize_filename(base_name)
                new_filename = base_name + ext
                if copy_mode:
                    new_path = os.path.join(target_dir, new_filename)
                else:
                    new_path = os.path.join(dir_name, new_filename)
                if len(new_path) > 259:
                    self.log("解决冲突后路径仍过长，跳过", "WARNING")
                    path_too_long = True
                    break
                attempt += 1

            if path_too_long:
                continue
            if attempt >= 10:
                self.log("无法生成不冲突的名称，跳过", "ERROR")
                continue

            rename_map.append((filepath, new_path))

        attempted_count = len(rename_map)
        if attempted_count == 0:
            self.log("没有需要重命名的文件")
            if failed_list:
                self.log(f"有 {len(failed_list)} 个文件因分析后变动被跳过", "WARNING")
            return

        self.log("命名映射预览：")
        for old, new in rename_map:
            self.log(f"{os.path.basename(old)} -> {os.path.basename(new)}")

        if not self.show_rename_confirmation_dialog(rename_map, folder, target_base, copy_mode):
            self.log("用户取消重命名")
            return

        success_count = 0
        exec_failed = []
        for old_path, new_path in rename_map:
            try:
                if copy_mode:
                    shutil.copy2(old_path, new_path)
                    self.log(f"复制并重命名：{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                else:
                    os.rename(old_path, new_path)
                    self.log(f"重命名：{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                success_count += 1
            except Exception as e:
                self.log(f"失败：{os.path.basename(old_path)} - {e}", "ERROR")
                exec_failed.append(old_path)

        fail_count = len(exec_failed) + len(failed_list)
        unprocessed = total_files - success_count - fail_count
        self.log("处理完成，统计信息：")
        self.log(f"  总文件数：{total_files}")
        self.log(f"  媒体文件数：{media_count}")
        self.log(f"  成功重命名：{success_count}")
        self.log(f"  失败（含跳过）：{fail_count}")
        self.log(f"  未处理（非媒体文件或无需重命名）：{unprocessed}")

        all_failed = exec_failed + failed_list
        if all_failed:
            msg = f"有 {len(all_failed)} 个文件未成功重命名，请检查日志。\n\n文件列表：\n"
            for f in all_failed[:10]:
                msg += f"• {os.path.basename(f)}\n"
            if len(all_failed) > 10:
                msg += f"... 等共 {len(all_failed)} 个文件。"
            messagebox.showwarning("重命名完成（有失败/跳过）", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoRenamer(root)
    root.mainloop()
