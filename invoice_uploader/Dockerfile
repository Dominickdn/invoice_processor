FROM python:3.10-slim

WORKDIR /app

COPY invoice_uploader/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY invoice_uploader/ .

COPY utils/ ./utils/

EXPOSE 5000

ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

CMD ["flask", "run"]