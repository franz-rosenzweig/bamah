FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bamah ./bamah
COPY tests ./tests

ENV PYTHONUNBUFFERED=1 BAMAH_DATA=/data
EXPOSE 8000
CMD ["uvicorn", "bamah.web:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
