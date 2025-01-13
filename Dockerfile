# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY charge_ok/ ./charge_ok/
COPY config.ini .
COPY supervisord.conf .

# 创建数据文件
RUN touch charge.csv

# 创建日志目录
RUN mkdir -p /var/log/

# 设置环境变量
ENV FLASK_APP=charge_ok/web.py
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 13333

# 启动命令
CMD ["supervisord", "-c", "supervisord.conf"] 