# 指定 basic image
FROM python:3.14
FROM mysql:9.7

# 設定工作目錄
WORKDIR /app

# copy 需要的套件列表
# COPY requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# COPY 其他必需的 code
COPY routes/ .
COPY models/ .

EXPOSE 5000

# start container 要報行的指令
CMD [ "python", "app.py" ]