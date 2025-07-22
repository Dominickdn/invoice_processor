FROM python:3.10-slim

# Install tesseract and poppler here
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ocr_worker/requirements.txt .

COPY ocr_worker/ .

COPY utils/ ./utils/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "main.py"]