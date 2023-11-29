FROM python:3.12.0
LABEL authors="davidmorgan"
# 设置工作目录
WORKDIR /app

# 复制当前目录的所有文件到镜像的/app目录下
COPY . /app

# 安装依赖项
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# 设置环境变量
ENV PYTHONPATH "${PYTHONPATH}:/app"

# 设置日志文件
RUN touch app.log

RUN chmod -R 777 /app

# 安装时区数据
RUN apt-get update && apt-get install -y \
    gcc

# 设置时区
ENV TZ=Asia/Shanghai

# 运行Python脚本
CMD python bot.py