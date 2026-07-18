
FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# 開發用
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
CMD ["flask", "run"]

# 正式用
# RUN pip install gunicorn
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
