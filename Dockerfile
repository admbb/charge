FROM python:3.9-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装 supervisor
RUN apt-get update && apt-get install -y supervisor tzdata

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制配置文件
COPY config.ini .

# 创建并设置权限
RUN mkdir -p /app/logs
RUN touch charge.csv
RUN chmod 777 /app
RUN chmod 666 config.ini charge.csv

# 复制项目文件
COPY *.py ./
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 13333

# 使用 supervisor 启动
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 