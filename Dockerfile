# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件
COPY requirements.txt .

# 安装依赖和系统库 (包括OCR所需)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 安装中文字体 (如果需要OCR中文)
# RUN apt-get update && apt-get install -y fonts-wqy-zenhei

# 运行主程序
CMD ["python", "src/main.py"]