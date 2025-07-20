# Invoice Processor

---

This project is a microservice-based invoice processing system built using Docker Compose. It ingests invoice files (PDFs or images), performs OCR, parses the extracted data, and stores it in a PostgreSQL database. All file handling is done using a local S3-compatible object store powered by MinIO. Communication between services is handled via RabbitMQ.

---

## Prerequisites
### 1. Docker & Docker Compose
Ensure Docker is installed and running on your machine.

Docker Compose is needed to orchestrate your multi-container services.

---

## Microservices Overview

### 1. **Invoice Uploader (Flask Web UI)**
- Starts a Flask server for uploading files.
- Files are uploaded to a MinIO bucket under the `process/` prefix.
- Provides options to enqueue files for processing via RabbitMQ.

### 2. **OCR Worker**
- Listens to the processing queue.
- Converts PDFs to images using `poppler` if needed.
- Runs Tesseract OCR on images to extract text.
- Publishes extracted text to another queue for parsing.

### 3. **Parser Worker**
- Listens to the parser queue.
- Parses structured invoice data (like invoice number, vendor, amount, etc.).
- Inserts structured data into a PostgreSQL database.
- Moves the processed file from `process/` to `processed/`.
- On failure, the file is moved to `failed/`.

---

## Stack

| Component     | Technology        |
|---------------|-------------------|
| File Storage  | MinIO (S3 API)    |
| Messaging     | RabbitMQ          |
| OCR Engine    | Tesseract + Poppler |
| Web UI        | Flask             |
| Database      | PostgreSQL        |
| Containerization | Docker Compose |

---

## Running the Project

### 1. Clone the repo:

git clone https://github.com/Dominickdn/invoice_processor.git
cd invoice-processor

### 2. Set up environment variables
Create a .env file in the root directory:

- an example is given just copy paste this into a .env file


### 3. Build and run the services:
docker-compose build --no-cache

docker-compose up -d

---

## Access

| Service          | URL                                                            |
| ---------------- | -------------------------------------------------------------- |
| Invoice Uploader | [http://localhost:5000](http://localhost:5000)                 |
| RabbitMQ UI      | [http://localhost:15672](http://localhost:15672) (guest/guest) |
| MinIO Console    | [http://localhost:9001](http://localhost:9001)                 |
| PostgreSQL       | localhost:5435 (via client)                                    |
---

## Message Queues
invoice_input: Files to process with OCR.

ocr_results: Extracted text to parse.

---

## Architecture Diagram
See architecture.mmd for the Mermaid.js source.

---

## Error Handling
Any file that fails at OCR or parsing stage is moved to failed/.

Logs are output to the console and container logs.

--- 
## Testing Locally

Upload a file via the UI (http://localhost:5000)
- Click choose files and select the files in the test_invoices folder supplied
- Click Upload
- Once files have been uploaded click the "Process All Files" button.

View Processed and Failed files (http://localhost:5000/status)

View Captured Invoices from Database (http://localhost:5000/invoices)

---

## Resetting the DB
To reset the PostgreSQL database run:

- docker-compose down -v
- docker-compose up -d

 This deletes all data in PostgreSQL and MinIO volumes.