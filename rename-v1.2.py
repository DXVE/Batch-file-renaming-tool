import os
import sys
import random
import string
import datetime
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from PIL import Image
from PIL.ExifTags import TAGS
import re  # 用于XMP解析

# 尝试导入 exifread（若未安装则跳过）
try:
    import exifread
    EXIFREAD_AVAILABLE = True
    EXIFREAD_VERSION = getattr(exifread, '__version__', 'unknown')
except ImportError:
    EXIFREAD_AVAILABLE = False
    EXIFREAD_VERSION = None


class PhotoRenamer:
    """照片视频批量重命名工具主类"""

    def __init__(self, root):
        """初始化主窗口及变量"""
        self.root = root
        self.root.title("照片视频批量重命名工具 V1.2")
        self.root.geometry("920x720")

        # 界面相关变量
        self.folder_path = tk.StringVar()                 # 源文件夹路径
        self.prefix = tk.StringVar()                      # 自定义前缀
        self.recursive = tk.BooleanVar(value=False)       # 是否递归子文件夹
        default_template = "{prefix}-{filetype}-{YYYY}-{MM}-{DD}-{hh}{mm}-{id}"
        self.template = tk.StringVar(value=default_template)  # 文件名模板
        self.copy_to_new = tk.BooleanVar(value=True)      # 是否复制到新目录
        self.target_folder = tk.StringVar()                # 目标文件夹路径
        self.verbose_log = tk.BooleanVar(value=False)     # 详细日志模式

        # 文件扩展名分类（互不重叠）
        self.image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        self.raw_exts = ('.arw', '.cr2', '.cr3', '.dng', '.nef', '.nrw',
                         '.orf', '.pef', '.raf', '.rw2', '.srw', '.x3f')
        self.digital_image_exts = ('.tiff', '.tif')
        self.video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',
                           '.m4v', '.mpg', '.mpeg')
        self.audio_exts = ('.mp3', '.wav', '.flac', '.aac', '.ogg',
                           '.m4a', '.wma')

        # 各类别勾选状态（默认勾选图像和视频）
        self.categories = {
            'image': tk.BooleanVar(value=True),
            'raw': tk.BooleanVar(value=False),
            'digital': tk.BooleanVar(value=False),
            'video': tk.BooleanVar(value=True),
            'audio': tk.BooleanVar(value=False)
        }

        self.create_widgets()          # 构建界面
        self.template.trace_add("write", lambda *args: self.update_preview())
        self.prefix.trace_add("write", lambda *args: self.update_preview())
        self.update_preview()           # 初始预览
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # ------------------------------------------------------------------
    # 界面构建相关方法
    # ------------------------------------------------------------------
    def create_widgets(self):
        """构建图形界面（控件从上到下排列）"""
        # 源文件夹选择
        frame_folder = tk.Frame(self.root)
        frame_folder.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_folder, text="源文件夹：").pack(side=tk.LEFT)
        tk.Entry(frame_folder, textvariable=self.folder_path).pack(
            side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        tk.Button(frame_folder, text="浏览", command=self.select_folder).pack(side=tk.LEFT)

        # 复制选项及目标文件夹
        frame_copy = tk.Frame(self.root)
        frame_copy.pack(pady=5, fill=tk.X, padx=5)

        self.copy_check = tk.Checkbutton(
            frame_copy, text="复制到新目录（保护原文件）",
            variable=self.copy_to_new, command=self.toggle_target_folder)
        self.copy_check.pack(side=tk.LEFT)

        self.target_entry = tk.Entry(frame_copy, textvariable=self.target_folder,
                                     state='disabled')
        self.target_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.target_button = tk.Button(frame_copy, text="浏览",
                                       command=self.select_target_folder,
                                       state='disabled')
        self.target_button.pack(side=tk.LEFT)

        # 自定义前缀输入
        frame_prefix = tk.Frame(self.root)
        frame_prefix.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_prefix, text="自定义前缀：").pack(side=tk.LEFT)
        tk.Entry(frame_prefix, textvariable=self.prefix, width=30).pack(
            side=tk.LEFT, padx=5)
        tk.Label(frame_prefix, text="(用于模板中的 {prefix}，留空则替换为空)").pack(side=tk.LEFT)

        # 递归选项
        frame_recursive = tk.Frame(self.root)
        frame_recursive.pack(pady=5, fill=tk.X, padx=5)
        tk.Checkbutton(frame_recursive, text="包含子文件夹",
                       variable=self.recursive).pack(side=tk.LEFT)

        # 详细日志模式复选框
        frame_verbose = tk.Frame(self.root)
        frame_verbose.pack(pady=5, fill=tk.X, padx=5)
        tk.Checkbutton(frame_verbose, text="详细日志模式（输出更多调试信息）",
                       variable=self.verbose_log).pack(side=tk.LEFT)

        # 文件类型选择（带扩展名说明）
        frame_categories = tk.LabelFrame(self.root, text="处理类型", padx=5, pady=5)
        frame_categories.pack(pady=5, fill=tk.X, padx=5)

        cb_image = tk.Checkbutton(
            frame_categories,
            text="图像类 (.jpg .jpeg .png .bmp .gif .webp)",
            variable=self.categories['image'], anchor='w')
        cb_image.pack(fill=tk.X)

        raw_exts_str = ' '.join(self.raw_exts)
        cb_raw = tk.Checkbutton(
            frame_categories,
            text=f"RAW类 {raw_exts_str}",
            variable=self.categories['raw'], anchor='w')
        cb_raw.pack(fill=tk.X)

        digital_exts_str = ' '.join(self.digital_image_exts)
        cb_digital = tk.Checkbutton(
            frame_categories,
            text=f"数字图像类 {digital_exts_str}",
            variable=self.categories['digital'], anchor='w')
        cb_digital.pack(fill=tk.X)

        video_exts_str = ' '.join(self.video_exts)
        cb_video = tk.Checkbutton(
            frame_categories,
            text=f"视频类 {video_exts_str}",
            variable=self.categories['video'], anchor='w')
        cb_video.pack(fill=tk.X)

        audio_exts_str = ' '.join(self.audio_exts)
        cb_audio = tk.Checkbutton(
            frame_categories,
            text=f"音频类 {audio_exts_str}",
            variable=self.categories['audio'], anchor='w')
        cb_audio.pack(fill=tk.X)

        # 文件名模板输入
        frame_template = tk.Frame(self.root)
        frame_template.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_template, text="文件名模板：").pack(side=tk.LEFT)
        template_entry = tk.Entry(frame_template, textvariable=self.template,
                                   width=50)
        template_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_template, text="(可包含占位符)").pack(side=tk.LEFT)

        # 占位符说明
        help_text = ("可用占位符: {YYYY}(四位年) {YY}(两位年) {MM}(月) {DD}(日) "
                     "{hh}(时) {mm}(分) {ss}(秒) {prefix}(自定义前缀) {id}(4位标识码) "
                     "{filetype}(文件类别: IMAGE/RAW/DIGITAL/VIDEO/AUDIO)")
        tk.Label(self.root, text=help_text, fg="blue", anchor="w").pack(
            pady=2, padx=5, fill=tk.X)

        # 显示当前使用的EXIF库
        if EXIFREAD_AVAILABLE:
            exif_status = f"✓ 使用 ExifRead {EXIFREAD_VERSION} (支持RAW/HEIC等)"
        else:
            exif_status = "⚠ 使用 PIL (基础EXIF支持，建议安装exifread: pip install exifread)"
        tk.Label(self.root, text=exif_status, fg="purple", anchor="w").pack(
            pady=2, padx=5, fill=tk.X)

        # 文件名预览标签
        self.preview_label = tk.Label(self.root, text="", fg="green",
                                      anchor="w", justify=tk.LEFT)
        self.preview_label.pack(pady=5, padx=5, fill=tk.X)

        # 开始重命名按钮
        tk.Button(self.root, text="开始重命名", command=self.start_rename,
                  bg="#4CAF50", fg="white").pack(pady=10)

        # 日志区域
        self.log_area = scrolledtext.ScrolledText(self.root, width=80,
                                                  height=14, state='normal')
        self.log_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        self.toggle_target_folder()

    def toggle_target_folder(self):
        """根据复制复选框状态启用/禁用目标文件夹控件"""
        if self.copy_to_new.get():
            self.target_entry.config(state='normal')
            self.target_button.config(state='normal')
        else:
            self.target_entry.config(state='disabled')
            self.target_button.config(state='disabled')

    def select_folder(self):
        """选择源文件夹"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def select_target_folder(self):
        """选择目标文件夹"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.target_folder.set(folder_selected)

    def log(self, message, level="INFO"):
        """向日志区添加一条消息并自动滚动到底部"""
        self.log_area.insert(tk.END, f"[{level}] {message}\n")
        self.log_area.see(tk.END)
        self.root.update()

    def update_preview(self):
        """根据当前模板和前缀更新文件名预览"""
        template = self.template.get().strip()
        prefix = self.prefix.get().strip()
        example_dt = datetime.datetime(2026, 3, 13, 14, 30, 45)
        example_id = "ABCD"
        example_filetype = "IMAGE"
        example_name = self.apply_template(template, example_dt, prefix,
                                           example_id, example_filetype)
        self.preview_label.config(text=f"示例：{example_name}.jpg")

    # ------------------------------------------------------------------
    # 文件处理核心方法
    # ------------------------------------------------------------------
    def get_filetype(self, ext):
        """
        根据扩展名返回文件类型标识（大写）
        返回值: 'IMAGE', 'RAW', 'DIGITAL', 'VIDEO', 'AUDIO' 之一，若未知则返回空字符串
        """
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
        """
        尝试多种常见格式解析日期字符串
        支持 ISO 格式（带 T 和时区），返回 datetime 对象，失败抛出 ValueError
        """
        date_str = str(date_str).strip()
        # 去除可能存在的时区偏移（如 +08:00）
        if '+' in date_str:
            date_str = date_str.split('+')[0]
        # 将常见的 T 分隔符替换为空格
        date_str = date_str.replace('T', ' ')
        # 尝试多种格式
        formats = [
            "%Y:%m:%d %H:%M:%S",   # 2023:04:26 11:16:22
            "%Y-%m-%d %H:%M:%S",   # 2023-04-26 11:16:22
            "%Y/%m/%d %H:%M:%S",   # 2023/04/26 11:16:22
            "%Y:%m:%d %H:%M",      # 2023:04:26 11:16
            "%Y-%m-%d %H:%M",      # 2023-04-26 11:16
            "%Y/%m/%d %H:%M",      # 2023/04/26 11:16
            "%Y:%m:%d",            # 2023:04:26
            "%Y-%m-%d",            # 2023-04-26
            "%Y/%m/%d",            # 2023/04/26
            "%Y-%m-%dT%H:%M:%S",   # 2023-04-26T11:16:22
            "%Y-%m-%dT%H:%M",       # 2023-04-26T11:16
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        raise ValueError(f"无法解析日期字符串: {date_str}")

    def parse_xmp_content(self, xmp_str):
        """
        从XMP字符串中提取创建日期
        返回 datetime 对象，失败返回 None
        """
        patterns = [
            r'xmp:CreateDate="([^"]+)"',
            r'xmp:DateCreated="([^"]+)"',
            r'xmp:MetadataDate="([^"]+)"',
            r'<xmp:CreateDate>([^<]+)</xmp:CreateDate>',
            r'<xmp:DateCreated>([^<]+)</xmp:DateCreated>',
            r'<xmp:MetadataDate>([^<]+)</xmp:MetadataDate>',
            r'photoshop:DateCreated="([^"]+)"',
            r'<photoshop:DateCreated>([^<]+)</photoshop:DateCreated>',
        ]
        for pattern in patterns:
            match = re.search(pattern, xmp_str)
            if match:
                date_str = match.group(1).strip()
                try:
                    dt = self.parse_date_string(date_str)
                    return dt
                except ValueError:
                    continue
        return None

    def parse_xmp_sidecar(self, filepath):
        """检查同目录下是否存在同名的 .xmp 文件，若有则解析其中的日期"""
        xmp_path = os.path.splitext(filepath)[0] + '.xmp'
        if os.path.exists(xmp_path):
            self.log(f"找到XMP侧边文件: {xmp_path}", "INFO")
            try:
                with open(xmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    xmp_str = f.read()
                if self.verbose_log.get():
                    self.log(f"[XMP侧边文件] 内容前200字符: {xmp_str[:200]}", "DEBUG")
                dt = self.parse_xmp_content(xmp_str)
                if dt:
                    self.log(f"[XMP侧边文件] 成功解析到日期 {dt}", "INFO")
                    return dt
                else:
                    self.log("[XMP侧边文件] 未找到有效日期", "INFO")
            except Exception as e:
                self.log(f"[XMP侧边文件] 读取失败: {e}", "WARNING")
        return None

    def get_media_datetime(self, filepath):
        """
        获取文件的拍摄/创建时间
        返回 (datetime, is_fallback, reason)
        is_fallback: True 表示未使用原始拍摄时间（DateTimeOriginal）
        reason: 日期来源说明（用于日志和弹窗）
        """
        ext = os.path.splitext(filepath)[1].lower()
        is_image_type = (ext in self.image_exts) or (ext in self.raw_exts) or (ext in self.digital_image_exts)

        # 非图像文件直接使用修改时间
        if not is_image_type:
            mtime = os.path.getmtime(filepath)
            dt = datetime.datetime.fromtimestamp(mtime)
            self.log(f"文件 {os.path.basename(filepath)} 不是图像类，使用修改时间", "INFO")
            return dt, True, "File Modification Time (non-image)"

        # 所有可能的EXIF日期标签（按优先级）
        date_tags_to_try = [
            ('EXIF DateTimeOriginal', 'DateTimeOriginal'),
            ('Image DateTime', 'Image DateTime'),
            ('EXIF DateTimeDigitized', 'DateTimeDigitized'),
            ('EXIF DateTime', 'EXIF DateTime'),
            ('EXIF_DateTimeOriginal', 'EXIF_DateTimeOriginal'),
            ('Image_DateTime', 'Image_DateTime'),
        ]

        # ---------- 方法1: exifread ----------
        if EXIFREAD_AVAILABLE:
            try:
                with open(filepath, 'rb') as f:
                    tags = exifread.process_file(f, details=True)
                    if self.verbose_log.get():
                        self.log(f"[ExifRead] 共读取到 {len(tags)} 个标签", "DEBUG")
                        tag_keys = list(tags.keys())
                        self.log(f"[ExifRead] 所有标签键名: {tag_keys}", "DEBUG")

                    # 尝试标准EXIF日期标签（详细模式下才输出找到的标签）
                    for tag_key, reason in date_tags_to_try:
                        if tag_key in tags:
                            dt_str = str(tags[tag_key])
                            if self.verbose_log.get():
                                self.log(f"[ExifRead] 找到标签 {tag_key} = {dt_str}", "DEBUG")
                            try:
                                dt = self.parse_date_string(dt_str)
                                is_fallback = ('Original' not in tag_key)
                                # 非详细模式下只输出最终使用的日期来源
                                if not is_fallback:
                                    self.log(f"文件 {os.path.basename(filepath)} 使用原始拍摄时间 {dt}", "INFO")
                                else:
                                    self.log(f"文件 {os.path.basename(filepath)} 使用其他日期标签 {tag_key}: {dt}", "INFO")
                                return dt, is_fallback, f"ExifRead: {tag_key}"
                            except ValueError as e:
                                if self.verbose_log.get():
                                    self.log(f"[ExifRead] 解析失败: {e}，尝试下一个标签", "WARNING")
                                continue

                    # 尝试查找XMP相关标签（可能存储为 Image XMP 或 Image XML 等）
                    xmp_tag_candidates = ['Image XMP', 'Image XML', 'XMP', 'XML']
                    for xmp_tag in xmp_tag_candidates:
                        if xmp_tag in tags:
                            xmp_str = str(tags[xmp_tag])
                            if self.verbose_log.get():
                                self.log(f"[ExifRead] 找到疑似XMP标签 {xmp_tag} (前200字符): {xmp_str[:200]}", "DEBUG")
                            dt = self.parse_xmp_content(xmp_str)
                            if dt:
                                self.log(f"文件 {os.path.basename(filepath)} 从XMP解析到原始拍摄时间 {dt}", "INFO")
                                return dt, False, f"XMP from {xmp_tag}"
                            else:
                                if self.verbose_log.get():
                                    self.log(f"[XMP] 未能从 {xmp_tag} 中解析到有效日期", "INFO")

                    # 尝试查找同名的XMP侧边文件
                    dt = self.parse_xmp_sidecar(filepath)
                    if dt:
                        self.log(f"文件 {os.path.basename(filepath)} 从XMP侧边文件解析到原始拍摄时间 {dt}", "INFO")
                        return dt, False, "XMP sidecar file"

                    if self.verbose_log.get():
                        self.log("[ExifRead] 未找到任何可解析的日期标签，尝试 PIL", "INFO")
            except Exception as e:
                if self.verbose_log.get():
                    self.log(f"[ExifRead] 读取失败: {e}，尝试 PIL", "WARNING")

        # ---------- 方法2: PIL ----------
        try:
            img = Image.open(filepath)
            if self.verbose_log.get():
                self.log(f"[PIL] 成功打开图像: {filepath}", "INFO")
            exif = img._getexif()
            if exif:
                if self.verbose_log.get():
                    self.log(f"[PIL] 获取到 EXIF 数据，包含 {len(exif)} 个标签", "INFO")
                # 将 PIL 标签 ID 转换为名称
                pil_tags = {}
                for tag_id, value in exif.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    pil_tags[tag_name] = value
                if self.verbose_log.get():
                    self.log("[PIL] 所有标签键名:", "DEBUG")
                    self.log(f"  {list(pil_tags.keys())}", "DEBUG")

                pil_priority = [('DateTimeOriginal', 'DateTimeOriginal'),
                                ('DateTime', 'DateTime'),
                                ('DateTimeDigitized', 'DateTimeDigitized')]
                for tag_name, reason in pil_priority:
                    if tag_name in pil_tags:
                        dt_str = str(pil_tags[tag_name])
                        if self.verbose_log.get():
                            self.log(f"[PIL] 找到标签 {tag_name} = {dt_str}", "DEBUG")
                        try:
                            dt = self.parse_date_string(dt_str)
                            is_fallback = (tag_name != 'DateTimeOriginal')
                            if not is_fallback:
                                self.log(f"文件 {os.path.basename(filepath)} 使用原始拍摄时间 {dt}", "INFO")
                            else:
                                self.log(f"文件 {os.path.basename(filepath)} 使用其他日期标签 {tag_name}: {dt}", "INFO")
                            return dt, is_fallback, f"PIL: {tag_name}"
                        except ValueError as e:
                            if self.verbose_log.get():
                                self.log(f"[PIL] 解析失败: {e}", "WARNING")
                            continue
            else:
                if self.verbose_log.get():
                    self.log("[PIL] 图像无 EXIF 数据", "INFO")
        except Exception as e:
            if self.verbose_log.get():
                self.log(f"[PIL] 处理时发生异常: {e}", "ERROR")

        # ---------- 最终回退：文件修改时间 ----------
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        self.log(f"文件 {os.path.basename(filepath)} 使用修改时间（回退）", "INFO")
        return dt, True, "File Modification Time (fallback)"

    def generate_unique_id(self, existing_ids):
        """生成4位唯一标识码（大写字母+数字）"""
        characters = string.ascii_uppercase + string.digits
        while True:
            new_id = ''.join(random.choices(characters, k=4))
            if new_id not in existing_ids:
                return new_id

    def sanitize_filename(self, filename):
        """替换文件名中的非法字符为下划线"""
        illegal_chars = r'\/:*?"<>|'
        for ch in illegal_chars:
            filename = filename.replace(ch, '_')
        return filename

    def apply_template(self, template, dt, prefix, file_id, filetype):
        """根据模板和实际数据生成基础文件名（不含扩展名）"""
        replacements = {
            "{YYYY}": dt.strftime("%Y"),
            "{YY}": dt.strftime("%y"),
            "{MM}": dt.strftime("%m"),
            "{DD}": dt.strftime("%d"),
            "{hh}": dt.strftime("%H"),
            "{mm}": dt.strftime("%M"),
            "{ss}": dt.strftime("%S"),
            "{prefix}": prefix,
            "{id}": file_id,
            "{filetype}": filetype
        }
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        return result

    def collect_all_files(self, folder, recursive):
        """收集文件夹内所有文件的完整路径"""
        all_files = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                for f in files:
                    all_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(folder):
                full = os.path.join(folder, f)
                if os.path.isfile(full):
                    all_files.append(full)
        return all_files

    def collect_media_files(self, folder, recursive):
        """根据勾选类别收集媒体文件"""
        media_files = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    if self._is_selected_category(ext):
                        media_files.append(full_path)
        else:
            for file in os.listdir(folder):
                full_path = os.path.join(folder, file)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(file)[1].lower()
                    if self._is_selected_category(ext):
                        media_files.append(full_path)
        return media_files

    def _is_selected_category(self, ext):
        """根据扩展名判断文件类别是否被勾选"""
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
        """返回文件相对于 base_folder 的目录路径（不含文件名）"""
        return os.path.relpath(os.path.dirname(full_path), base_folder)

    # ------------------------------------------------------------------
    # 对话框方法
    # ------------------------------------------------------------------
    def show_ignored_files_dialog(self, ignored_files, folder, total_files,
                                   ignored_count):
        """显示被忽略的非媒体文件列表对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("忽略文件列表")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = (f"当前目录下共有 {total_files} 个文件，其中 {ignored_count} 个"
               "不是支持的媒体格式，将不会被处理：")
        tk.Label(dialog, text=msg, wraplength=550, justify=tk.LEFT).pack(
            pady=10, padx=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
                             font=("Courier", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for f in ignored_files:
            listbox.insert(tk.END, f)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        result = [False]

        def on_continue():
            result[0] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(btn_frame, text="继续", command=on_continue, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(
            side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    def show_rename_confirmation_dialog(self, rename_map, folder, target_base,
                                        copy_mode):
        """显示重命名映射确认对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("确认重命名")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = f"将重命名以下 {len(rename_map)} 个文件："
        tk.Label(dialog, text=msg, wraplength=650, justify=tk.LEFT).pack(
            pady=10, padx=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
                             font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for old_path, new_path in rename_map:
            old_rel = os.path.relpath(old_path, folder)
            if copy_mode:
                new_rel = os.path.relpath(new_path, target_base)
            else:
                new_rel = os.path.relpath(new_path, folder)
            listbox.insert(tk.END, f"{old_rel} -> {new_rel}")

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        result = [False]

        def on_confirm():
            result[0] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(btn_frame, text="确定", command=on_confirm, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(
            side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    def show_fallback_files_dialog(self, fallback_files, folder, previews_dict):
        """
        显示使用其他日期或修改时间的文件列表对话框
        显示格式：原文件名 -> 示例新文件名 [日期来源原因]
        支持双击打开文件所在文件夹
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("使用其他日期或修改时间的文件列表")
        dialog.geometry("700x400")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = (f"以下 {len(fallback_files)} 个文件未能使用原始拍摄时间"
               "（将使用其他日期或修改时间），预览新文件名如下：")
        tk.Label(dialog, text=msg, wraplength=650, justify=tk.LEFT).pack(
            pady=10, padx=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set,
                             font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for f in fallback_files:
            old_name = os.path.basename(f)
            preview_info = previews_dict.get(f, {})
            preview_name = preview_info.get('preview', '未知')
            reason = preview_info.get('reason', '未知原因')
            listbox.insert(tk.END, f"{old_name} -> {preview_name}  [{reason}]")

        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                file_path = fallback_files[index]
                if os.name == 'nt':
                    os.startfile(os.path.dirname(file_path))
                else:
                    import subprocess
                    try:
                        subprocess.Popen(['xdg-open', os.path.dirname(file_path)])
                    except Exception:
                        pass

        listbox.bind("<Double-Button-1>", on_double_click)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        result = [False]

        def on_continue():
            result[0] = True
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(btn_frame, text="继续", command=on_continue, width=10,
                  bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(
            side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def start_rename(self):
        """执行重命名主流程（添加了文件分隔线以便日志观察）"""
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

        if EXIFREAD_AVAILABLE:
            self.log(f"使用 ExifRead {EXIFREAD_VERSION} 读取EXIF "
                     "(支持RAW/HEIC等格式)", "INFO")
        else:
            self.log("使用 PIL 读取EXIF (建议安装exifread以获得更好的RAW文件支持: "
                     "pip install exifread)", "INFO")

        all_files = self.collect_all_files(folder, self.recursive.get())
        total_files = len(all_files)
        media_files = self.collect_media_files(folder, self.recursive.get())
        media_count = len(media_files)
        ignored_count = total_files - media_count

        if ignored_count > 0:
            ignored_set = set(all_files) - set(media_files)
            ignored_list = sorted(ignored_set)
            rel_ignored = [os.path.relpath(f, folder) for f in ignored_list]
            if not self.show_ignored_files_dialog(rel_ignored, folder,
                                                  total_files, ignored_count):
                self.log("用户取消重命名", "INFO")
                return
            self.log(f"忽略非媒体文件 {ignored_count} 个", "INFO")

        if not media_files:
            self.log("没有找到图片、视频或音频文件", "WARNING")
            return

        self.log(f"找到 {media_count} 个媒体文件，开始处理...")
        if copy_mode:
            self.log(f"将复制到目标文件夹：{target_base}，并保持子目录结构")

        # 第一阶段：收集使用其他日期或修改时间的文件及其原因，同时生成预览新文件名
        fallback_files = []
        fallback_previews = {}  # 键：文件路径，值：{'preview': 预览文件名, 'reason': 原因}
        for filepath in media_files:
            self.log(f"------------------ 处理文件: {os.path.basename(filepath)} ------------------", "INFO")
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.jpeg':
                ext = '.jpg'
            dt, is_fallback, reason = self.get_media_datetime(filepath)
            if is_fallback:
                fallback_files.append(filepath)
                # 生成预览新文件名（使用临时ID "XXXX"）
                filetype = self.get_filetype(ext)
                prefix = self.prefix.get().strip()
                template = self.template.get().strip()
                # 临时生成一个预览文件名，不加入existing_ids集合
                preview_name = self.apply_template(template, dt, prefix, "XXXX", filetype)
                preview_name = self.sanitize_filename(preview_name) + ext
                fallback_previews[filepath] = {'preview': preview_name, 'reason': reason}

        if fallback_files:
            if not self.show_fallback_files_dialog(fallback_files, folder, fallback_previews):
                self.log("用户取消重命名", "INFO")
                return
            self.log(f"有 {len(fallback_files)} 个文件使用其他日期或修改时间", "INFO")

        # 第二阶段：生成重命名映射（再次添加分隔线）
        existing_ids = set()
        rename_map = []
        template = self.template.get().strip()
        if not template:
            messagebox.showerror("错误", "文件名模板不能为空")
            return

        for filepath in media_files:
            self.log(f"------------------ 重命名映射: {os.path.basename(filepath)} ------------------", "INFO")
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.jpeg':
                ext = '.jpg'

            dt, _, _ = self.get_media_datetime(filepath)  # 再次调用，获取时间
            new_id = self.generate_unique_id(existing_ids)
            existing_ids.add(new_id)

            filetype = self.get_filetype(ext)
            prefix = self.prefix.get().strip()
            base_name = self.apply_template(template, dt, prefix, new_id,
                                            filetype)
            base_name = self.sanitize_filename(base_name)
            new_filename = base_name + ext

            if copy_mode:
                rel_dir = self.get_relative_path(filepath, folder)
                target_dir = (os.path.join(target_base, rel_dir)
                              if rel_dir != "." else target_base)
                os.makedirs(target_dir, exist_ok=True)
                new_path = os.path.join(target_dir, new_filename)
            else:
                dir_name = os.path.dirname(filepath)
                new_path = os.path.join(dir_name, new_filename)

            if not copy_mode and new_path == filepath:
                self.log(f"文件 {os.path.basename(filepath)} 无需重命名", "INFO")
                continue

            # 处理文件名冲突
            attempt = 0
            while os.path.exists(new_path) and attempt < 10:
                new_id = self.generate_unique_id(existing_ids)
                existing_ids.add(new_id)
                base_name = self.apply_template(template, dt, prefix, new_id,
                                                filetype)
                base_name = self.sanitize_filename(base_name)
                new_filename = base_name + ext
                if copy_mode:
                    new_path = os.path.join(target_dir, new_filename)
                else:
                    new_path = os.path.join(dir_name, new_filename)
                attempt += 1

            if attempt >= 10:
                self.log(f"文件 {os.path.basename(filepath)} 无法生成不冲突的新名称，跳过",
                         "ERROR")
                continue

            rename_map.append((filepath, new_path))

        attempted_count = len(rename_map)
        if attempted_count == 0:
            self.log("没有需要重命名的文件", "INFO")
            return

        self.log("以下是所有文件的命名映射（请确认）：")
        for old, new in rename_map:
            self.log(f"{os.path.basename(old)} -> {os.path.basename(new)}")

        if not self.show_rename_confirmation_dialog(rename_map, folder,
                                                     target_base, copy_mode):
            self.log("用户取消重命名", "INFO")
            return

        # 执行重命名/复制
        success_count = 0
        for old_path, new_path in rename_map:
            try:
                if copy_mode:
                    shutil.copy2(old_path, new_path)
                    self.log(f"成功复制并重命名：{os.path.basename(old_path)} "
                             f"-> {os.path.basename(new_path)}")
                else:
                    os.rename(old_path, new_path)
                    self.log(f"成功重命名：{os.path.basename(old_path)} "
                             f"-> {os.path.basename(new_path)}")
                success_count += 1
            except Exception as e:
                self.log(f"失败：{os.path.basename(old_path)} - {e}", "ERROR")

        fail_count = attempted_count - success_count
        unprocessed = total_files - success_count - fail_count
        self.log("处理完成，统计信息：")
        self.log(f"  总文件数：{total_files}")
        self.log(f"  媒体文件数：{media_count}")
        self.log(f"  成功重命名：{success_count}")
        self.log(f"  失败：{fail_count}")
        self.log(f"  未处理（非媒体文件或无需重命名）：{unprocessed}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoRenamer(root)
    root.mainloop()
