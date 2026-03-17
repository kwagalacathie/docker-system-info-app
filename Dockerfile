FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

# Use Gunicorn (WSGI server) for Flask
# --bind 0.0.0.0:80 = listen on all interfaces, port 80
# --workers 2 = use 2 worker processes (adjust based on CPU)
# app:app = module:app instance
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "2", "app:app"]