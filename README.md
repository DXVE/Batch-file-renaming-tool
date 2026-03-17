# 🧰    文件批量重命名工具    Batch-file-renaming-tool    

一个功能强大的图形化批量重命名工具，专为摄影爱好者和多媒体管理者设计。支持图片、RAW格式、数字图像、视频、音频等多种文件类型，可基于文件元数据（EXIF拍摄时间或修改时间）自动生成规范的文件名，并提供灵活的模板定制和安全的复制模式。

<p align="center">
<img src="https://github.com/DXVE/Batch-file-renaming-tool/blob/main/images/%E7%A4%BA%E4%BE%8B%E5%9B%BE%E7%89%87-v1.1.png?raw=true" width="576" height="470.5">
</p>

## ✨ 功能特点

- **🕝 智能时间获取**  
  优先读取图片的 EXIF 拍摄时间（DateTimeOriginal），如无则使用文件的修改时间。

- **📁 支持自定义文件名模板**  
  允许通过占位符自由组合文件名，例如 `{prefix}-{YYYY}-{MM}-{DD}-{hh}{mm}-{id}` 可生成 `旅行-2025-03-16-1430-A1B2.jpg`。  
  支持的文件名模板：
  - `{YYYY}`、`{YY}`、`{MM}`、`{DD}`、`{hh}`、`{mm}`、`{ss}`（日期时间）
  - `{prefix}`（自定义前缀）
  - `{id}`（4位唯一标识码）
  - `{filetype}`（文件类别（根据传入文件自动标识）：IMAGE、RAW、DIGITAL、VIDEO、AUDIO）

- **🔍️ 重命名模板实时预览**  
  修改模板或前缀时，界面立即显示示例文件名，所见即所得。  

- **🆔 唯一的标识码系统**  
  工具支持生成标识码，同一处理目录下各个文件标识码唯一；如果目标目录已存在同名文件，程序会自动重新生成标识码（最多尝试10次），以避免重复的文件名。

- **🖥️ 兼容的命名系统**  
  文件名中的非法字符```（\ / : * ? " < > |）```会被自动替换为下划线，以确保系统兼容。

- **🖼️ 支持丰富的文件类型**
  - 图像格式： ` .jpg, .jpeg, .png, .bmp, .gif, .webp `
  - 视频格式： ` .mp4, .avi, .mov, .mkv, .flv, .wmv, .m4v, .mpg, .mpeg `
  - RAW格式： ` .arw, .cr2, .cr3, .dng, .nef, .nrw, .orf, .pef, .raf, .rw2, .srw, .x3f `
  - 数字图像格式： ` .tiff, .tif `
  - 音频格式： ` .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma `
  - **支持文件格式自定义，如需扩展支持的文件类型，可在代码中修改对应的扩展名组类（如 image_exts）。**
  ```bash
  self.image_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
  self.raw_exts = ('.arw', '.cr2', '.cr3', '.dng', '.nef', '.nrw', '.orf', '.pef', '.raf', '.rw2', '.srw', '.x3f')
  self.digital_image_exts = ('.tiff', '.tif')
  self.video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg')
  self.audio_exts = ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma')

- **☑️ 支持按文件类型筛选**  
  支持对图像、音视频、RAW文件以及数字文件进行处理，默认勾选图像类和视频类，可根据需要勾选需要处理的类别，避免无关文件被误操作。

- **📋 安全的复制模式**  
  支持重命名时“复制到新目录”，在目标文件夹下重建原目录结构并重命名，原文件完全保留无修改，避免数据丢失风险。

- **🗂️ 支持递归处理子文件夹**  
  勾选后自动遍历所有子目录，保持原有文件组织。  

- **📊 详细的日志记录**  
  操作前弹出确认窗口，完整列出所有将被重命名（或忽略）的文件，手动确认后再执行；  
  执行完成后会生成统计信息：  
  ```
  [INFO] 处理完成，统计信息：
  [INFO]   总文件数：66
  [INFO]   媒体文件数：66
  [INFO]   成功重命名：66
  [INFO]   失败：0
  [INFO]   未处理（非媒体文件或无需重命名）：0
  ```


## 📦 安装与运行

### 🛠 环境要求
- Python 3.14.3 或更高版本
  - <html>https://www.python.org/downloads/</html>
  
- 依赖库：`Pillow`（用于读取图片 EXIF）
  - ```pip install Pillow```

- 依赖库：`exifread`（可选、建议安装，用于RAW/HEIC文件读取处理）（未安装时自动降级使用 Pillow 处理）
  - ```pip install exifread```

### ⚙️ 安装步骤
1. 克隆或下载本仓库代码（*或在`releases`中下载最新版本的`.py`文件*）
   
2. 安装```Python```

3. 安装依赖```Pillow```：
   ```bash
   pip install Pillow
   
4. 安装依赖```exifread```：
   ```bash
   pip install exifread
   
5. 运行程序：
   ```bash
   python rename-<version>.py
6. 开始整理吧！

## 🥰 如果这个工具对你有帮助，欢迎给个 ⭐ Star！

