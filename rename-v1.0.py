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

class PhotoRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("照片视频批量重命名工具 V1.0")
        self.root.geometry("920x720")

        # 源文件夹路径
        self.folder_path = tk.StringVar()
        # 自定义前缀（用于模板中的 {prefix} 占位符）
        self.prefix = tk.StringVar()
        # 是否递归处理子文件夹
        self.recursive = tk.BooleanVar(value=False)
        # 文件名模板（固定默认值，不保存配置文件）
        default_template = "{prefix}-{YYYY}-{MM}-{DD}-{hh}{mm}-{id}"
        self.template = tk.StringVar(value=default_template)
        # 是否复制到新目录（默认勾选，保护原文件）
        self.copy_to_new = tk.BooleanVar(value=True)
        # 目标文件夹路径（当复制模式启用时使用）
        self.target_folder = tk.StringVar()

        # 定义各类文件的扩展名（互不重叠）
        self.image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        self.raw_exts = ('.arw', '.cr2', '.cr3', '.dng', '.nef', '.nrw', '.orf', '.pef', '.raf', '.rw2', '.srw', '.x3f')
        self.digital_image_exts = ('.tiff', '.tif')
        self.video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg')
        self.audio_exts = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma')

        # 各类别对应的布尔变量（默认勾选图像和视频）
        self.categories = {
            'image': tk.BooleanVar(value=True),
            'raw': tk.BooleanVar(value=False),
            'digital': tk.BooleanVar(value=False),
            'video': tk.BooleanVar(value=True),
            'audio': tk.BooleanVar(value=False)
        }

        # 创建界面组件
        self.create_widgets()

        # 绑定模板和前缀的修改事件，实时更新预览
        self.template.trace_add("write", lambda *args: self.update_preview())
        self.prefix.trace_add("write", lambda *args: self.update_preview())
        # 初始预览
        self.update_preview()

        # 窗口关闭时不保存任何配置
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def create_widgets(self):
        """构建图形界面"""
        # 源文件夹选择
        frame_folder = tk.Frame(self.root)
        frame_folder.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_folder, text="源文件夹：").pack(side=tk.LEFT)
        # 移除固定宽度，使输入框可随窗口拉伸
        tk.Entry(frame_folder, textvariable=self.folder_path).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        tk.Button(frame_folder, text="浏览", command=self.select_folder).pack(side=tk.LEFT)

        # 复制选项及目标文件夹
        frame_copy = tk.Frame(self.root)
        frame_copy.pack(pady=5, fill=tk.X, padx=5)

        self.copy_check = tk.Checkbutton(frame_copy, text="复制到新目录（保护原文件）",
                                         variable=self.copy_to_new,
                                         command=self.toggle_target_folder)
        self.copy_check.pack(side=tk.LEFT)

        # 目标文件夹输入框也设为可拉伸
        self.target_entry = tk.Entry(frame_copy, textvariable=self.target_folder, state='disabled')
        self.target_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.target_button = tk.Button(frame_copy, text="浏览", command=self.select_target_folder, state='disabled')
        self.target_button.pack(side=tk.LEFT)

        # 自定义前缀输入
        frame_prefix = tk.Frame(self.root)
        frame_prefix.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_prefix, text="自定义前缀：").pack(side=tk.LEFT)
        tk.Entry(frame_prefix, textvariable=self.prefix, width=30).pack(side=tk.LEFT, padx=5)
        tk.Label(frame_prefix, text="(用于模板中的 {prefix}，留空则替换为空)").pack(side=tk.LEFT)

        # 递归选项
        frame_recursive = tk.Frame(self.root)
        frame_recursive.pack(pady=5, fill=tk.X, padx=5)

        tk.Checkbutton(frame_recursive, text="包含子文件夹", variable=self.recursive).pack(side=tk.LEFT)

        # 文件类型选择（垂直排列，带扩展名说明）
        frame_categories = tk.LabelFrame(self.root, text="处理类型", padx=5, pady=5)
        frame_categories.pack(pady=5, fill=tk.X, padx=5)

        # 图像类
        cb_image = tk.Checkbutton(frame_categories, text="图像类 (.jpg .jpeg .png .bmp .gif .webp)",
                                   variable=self.categories['image'], anchor='w')
        cb_image.pack(fill=tk.X)

        # RAW类
        raw_exts_str = ' '.join(self.raw_exts)
        cb_raw = tk.Checkbutton(frame_categories, text=f"RAW类 {raw_exts_str}",
                                variable=self.categories['raw'], anchor='w')
        cb_raw.pack(fill=tk.X)

        # 数字图像类
        digital_exts_str = ' '.join(self.digital_image_exts)
        cb_digital = tk.Checkbutton(frame_categories, text=f"数字图像类 {digital_exts_str}",
                                    variable=self.categories['digital'], anchor='w')
        cb_digital.pack(fill=tk.X)

        # 视频类
        video_exts_str = ' '.join(self.video_exts)
        cb_video = tk.Checkbutton(frame_categories, text=f"视频类 {video_exts_str}",
                                  variable=self.categories['video'], anchor='w')
        cb_video.pack(fill=tk.X)

        # 音频类
        audio_exts_str = ' '.join(self.audio_exts)
        cb_audio = tk.Checkbutton(frame_categories, text=f"音频类 {audio_exts_str}",
                                  variable=self.categories['audio'], anchor='w')
        cb_audio.pack(fill=tk.X)

        # 文件名模板输入
        frame_template = tk.Frame(self.root)
        frame_template.pack(pady=5, fill=tk.X, padx=5)

        tk.Label(frame_template, text="文件名模板：").pack(side=tk.LEFT)
        template_entry = tk.Entry(frame_template, textvariable=self.template, width=50)
        template_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_template, text="(可包含占位符)").pack(side=tk.LEFT)

        # 占位符说明（已包含 {filetype}）
        help_text = ("可用占位符: {YYYY}(四位年) {YY}(两位年) {MM}(月) {DD}(日) "
                     "{hh}(时) {mm}(分) {ss}(秒) {prefix}(自定义前缀) {id}(4位标识码) {filetype}(文件类别: image/raw/digital/video/audio)")
        tk.Label(self.root, text=help_text, fg="blue", anchor="w").pack(pady=2, padx=5, fill=tk.X)

        # 文件名预览标签
        self.preview_label = tk.Label(self.root, text="", fg="green", anchor="w", justify=tk.LEFT)
        self.preview_label.pack(pady=5, padx=5, fill=tk.X)

        # 开始重命名按钮
        tk.Button(self.root, text="开始重命名", command=self.start_rename, bg="#4CAF50", fg="white").pack(pady=10)

        # 日志区域
        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=14, state='normal')
        self.log_area.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # 根据初始勾选状态设置目标文件夹输入框状态
        self.toggle_target_folder()

    def toggle_target_folder(self):
        """根据复制复选框的状态启用或禁用目标文件夹相关控件"""
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
        """向日志区域添加一条消息并自动滚动到底部"""
        self.log_area.insert(tk.END, f"[{level}] {message}\n")
        self.log_area.see(tk.END)
        self.root.update()

    def update_preview(self):
        """根据当前模板和前缀更新文件名预览（使用示例文件类型 image）"""
        template = self.template.get().strip()
        prefix = self.prefix.get().strip()
        # 使用固定示例时间 2026-03-13 14:30:45
        example_dt = datetime.datetime(2026, 3, 13, 14, 30, 45)
        example_id = "ABCD"
        example_filetype = "image"  # 预览时使用 image 类型
        example_name = self.apply_template(template, example_dt, prefix, example_id, example_filetype)
        self.preview_label.config(text=f"示例：{example_name}.jpg")

    def get_filetype(self, ext):
        """
        根据扩展名返回对应的文件类型标识。
        返回值为 'image', 'raw', 'digital', 'video', 'audio' 之一。
        若扩展名不在已知类别中，返回空字符串。
        """
        if ext in self.image_exts:
            return "image"
        elif ext in self.raw_exts:
            return "raw"
        elif ext in self.digital_image_exts:
            return "digital"
        elif ext in self.video_exts:
            return "video"
        elif ext in self.audio_exts:
            return "audio"
        else:
            return ""

    def get_media_datetime(self, filepath):
        """
        获取文件的拍摄/创建时间：
        - 对于可读 EXIF 的图片，优先返回 DateTimeOriginal；
        - 其他情况返回文件的修改时间。
        返回 datetime 对象。
        """
        try:
            img = Image.open(filepath)
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        dt_str = value
                        return datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    elif tag == "DateTime":
                        dt_str = value
                        return datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass

        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        self.log(f"文件 {os.path.basename(filepath)} 使用修改时间：{dt.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        return dt

    def generate_unique_id(self, existing_ids):
        """
        生成一个 4 位（大写字母+数字）的唯一标识码，确保不与 existing_ids 重复。
        """
        characters = string.ascii_uppercase + string.digits
        while True:
            new_id = ''.join(random.choices(characters, k=4))
            if new_id not in existing_ids:
                return new_id

    def sanitize_filename(self, filename):
        r"""
        替换文件名中的非法字符（Windows 下不允许 \ / : * ? " < > |）为下划线。
        使用原始字符串避免转义问题。
        """
        illegal_chars = r'\/:*?"<>|'
        for ch in illegal_chars:
            filename = filename.replace(ch, '_')
        return filename

    def apply_template(self, template, dt, prefix, file_id, filetype):
        """
        根据模板和实际数据生成基础文件名（不含扩展名）。
        模板支持以下占位符：
            {YYYY}, {YY}, {MM}, {DD}, {hh}, {mm}, {ss}, {prefix}, {id}, {filetype}
        其他文本原样保留。
        """
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
        """递归或非递归收集文件夹内的所有文件，返回完整路径列表"""
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
        """
        根据用户勾选的类别收集文件。
        返回符合勾选类别的文件列表。
        """
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
        """
        根据扩展名判断该文件所属类别是否被用户勾选。
        """
        if ext in self.image_exts:
            return self.categories['image'].get()
        elif ext in self.raw_exts:
            return self.categories['raw'].get()
        elif ext in self.digital_image_exts:
            return self.categories['digital'].get()
        elif ext in self.video_exts:
            return self.categories['video'].get()
        elif ext in self.audio_exts:
            return self.categories['audio'].get()
        else:
            return False

    def get_relative_path(self, full_path, base_folder):
        """返回文件相对于 base_folder 的目录路径（不含文件名）"""
        return os.path.relpath(os.path.dirname(full_path), base_folder)

    def show_ignored_files_dialog(self, ignored_files, folder, total_files, ignored_count):
        """
        显示一个带滚动条的模态对话框，列出所有被忽略的文件。
        返回 True 表示用户选择继续，False 表示取消。
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("忽略文件列表")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = f"当前目录下共有 {total_files} 个文件，其中 {ignored_count} 个不是支持的媒体格式，将不会被处理："
        tk.Label(dialog, text=msg, wraplength=550, justify=tk.LEFT).pack(pady=10, padx=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Courier", 10))
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

        tk.Button(btn_frame, text="继续", command=on_continue, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    def show_rename_confirmation_dialog(self, rename_map, folder, target_base, copy_mode):
        """
        显示一个带滚动条的模态对话框，列出所有将被重命名的文件映射。
        返回 True 表示用户确认，False 表示取消。
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("确认重命名")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = f"将重命名以下 {len(rename_map)} 个文件："
        tk.Label(dialog, text=msg, wraplength=650, justify=tk.LEFT).pack(pady=10, padx=10)

        frame = tk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=listbox.yview)

        # 填充映射列表
        for old_path, new_path in rename_map:
            old_rel = os.path.relpath(old_path, folder)
            if copy_mode:
                # 目标文件显示相对于目标根目录的路径
                new_rel = os.path.relpath(new_path, target_base)
            else:
                # 目标文件显示相对于源文件夹的路径
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

        tk.Button(btn_frame, text="确定", command=on_confirm, width=10, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result[0]

    def start_rename(self):
        """执行重命名主流程"""
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择一个有效的源文件夹")
            return

        # 处理复制模式
        copy_mode = self.copy_to_new.get()
        target_base = None
        if copy_mode:
            target_base = self.target_folder.get().strip()
            if not target_base:
                messagebox.showerror("错误", "请选择一个目标文件夹")
                return
            os.makedirs(target_base, exist_ok=True)

        # 清空日志
        self.log_area.delete(1.0, tk.END)

        # 统计所有文件及媒体文件
        all_files = self.collect_all_files(folder, self.recursive.get())
        total_files = len(all_files)
        media_files = self.collect_media_files(folder, self.recursive.get())
        media_count = len(media_files)
        ignored_count = total_files - media_count

        # 存在被忽略文件时弹出详细列表窗口
        if ignored_count > 0:
            ignored_set = set(all_files) - set(media_files)
            ignored_list = sorted(ignored_set)
            rel_ignored = [os.path.relpath(f, folder) for f in ignored_list]

            if not self.show_ignored_files_dialog(rel_ignored, folder, total_files, ignored_count):
                self.log("用户取消重命名", "INFO")
                return
            self.log(f"忽略非媒体文件 {ignored_count} 个", "INFO")

        if not media_files:
            self.log("没有找到图片、视频或音频文件", "WARNING")
            return

        self.log(f"找到 {media_count} 个媒体文件，开始处理...")
        if copy_mode:
            self.log(f"将复制到目标文件夹：{target_base}，并保持子目录结构")

        # 准备重命名映射
        existing_ids = set()
        rename_map = []  # 元素为 (原路径, 新路径)
        template = self.template.get().strip()
        if not template:
            messagebox.showerror("错误", "文件名模板不能为空")
            return

        for filepath in media_files:
            ext = os.path.splitext(filepath)[1].lower()
            # 统一 .jpeg 为 .jpg
            if ext == '.jpeg':
                ext = '.jpg'

            dt = self.get_media_datetime(filepath)
            new_id = self.generate_unique_id(existing_ids)
            existing_ids.add(new_id)

            # 获取文件类型标识
            filetype = self.get_filetype(ext)

            prefix = self.prefix.get().strip()
            base_name = self.apply_template(template, dt, prefix, new_id, filetype)
            base_name = self.sanitize_filename(base_name)
            new_filename = base_name + ext

            # 确定目标路径
            if copy_mode:
                rel_dir = self.get_relative_path(filepath, folder)
                target_dir = os.path.join(target_base, rel_dir) if rel_dir != "." else target_base
                os.makedirs(target_dir, exist_ok=True)
                new_path = os.path.join(target_dir, new_filename)
            else:
                dir_name = os.path.dirname(filepath)
                new_path = os.path.join(dir_name, new_filename)

            # 如果原文件无需改名，跳过
            if not copy_mode and new_path == filepath:
                self.log(f"文件 {os.path.basename(filepath)} 无需重命名", "INFO")
                continue

            # 处理目标文件名冲突（最多尝试10次重新生成ID）
            attempt = 0
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
                attempt += 1

            if attempt >= 10:
                self.log(f"文件 {os.path.basename(filepath)} 无法生成不冲突的新名称，跳过", "ERROR")
                continue

            rename_map.append((filepath, new_path))

        attempted_count = len(rename_map)
        if attempted_count == 0:
            self.log("没有需要重命名的文件", "INFO")
            return

        # 记录完整映射到日志
        self.log("以下是所有文件的命名映射（请确认）：")
        for old, new in rename_map:
            self.log(f"{os.path.basename(old)} -> {os.path.basename(new)}")

        # 使用新对话框确认重命名
        if not self.show_rename_confirmation_dialog(rename_map, folder, target_base, copy_mode):
            self.log("用户取消重命名", "INFO")
            return

        # 执行重命名/复制操作
        success_count = 0
        for old_path, new_path in rename_map:
            try:
                if copy_mode:
                    shutil.copy2(old_path, new_path)
                    self.log(f"成功复制并重命名：{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                else:
                    os.rename(old_path, new_path)
                    self.log(f"成功重命名：{os.path.basename(old_path)} -> {os.path.basename(new_path)}")
                success_count += 1
            except Exception as e:
                self.log(f"失败：{os.path.basename(old_path)} - {e}", "ERROR")

        # 最终统计
        fail_count = attempted_count - success_count
        unprocessed = total_files - success_count - fail_count
        self.log(f"处理完成，统计信息：")
        self.log(f"  总文件数：{total_files}")
        self.log(f"  媒体文件数：{media_count}")
        self.log(f"  成功重命名：{success_count}")
        self.log(f"  失败：{fail_count}")
        self.log(f"  未处理（非媒体文件或无需重命名）：{unprocessed}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoRenamer(root)
    root.mainloop()
