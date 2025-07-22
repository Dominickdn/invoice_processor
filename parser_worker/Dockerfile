FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
 && rm -rf /var/lib/apt/lists/*

COPY parser_worker/requirements.txt .

COPY parser_worker/ .

COPY utils/ ./utils/

RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "-u", "main.py"]
