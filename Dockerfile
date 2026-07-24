FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "taskflow.wsgi:application", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120"]