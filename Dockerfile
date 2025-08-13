# 使用官方Python 3.11运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件
COPY requirements.txt .

# 安装系统依赖 (包括OCR所需) 和 Python 依赖
# 使用 shell 折行符 \ 使命令更易读
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        # OCR 引擎
        tesseract-ocr \
        # OCR 引擎开发文件
        libtesseract-dev \
        # 图像处理库 (Pillow依赖)
        libjpeg-dev \
        zlib1g-dev \
        # 文件监控可能需要的编译工具 (watchdog)
        gcc \
        # YAML配置文件处理可能需要
        pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    # 安装 Python 依赖
    && pip install --no-cache-dir -r requirements.txt

# 复制项目代码
# .dockerignore 应该被用来排除不必要的文件（如 .git, __pycache__ 等）
COPY . .

# 安装中文字体 (如果需要OCR中文或生成中文报告)
# RUN apt-get update && apt-get install -y fonts-wqy-zenhei

# 运行主程序
CMD ["python", "src/main.py"]