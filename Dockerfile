
FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

RUN pip install gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
