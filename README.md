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
- Reports status to Redis.

### 3. **Parser Worker**
- Listens to the parser queue.
- Parses structured invoice data (like invoice number, vendor, amount, etc.).
- Inserts structured data into a PostgreSQL database.
- Moves the processed file from `process/` to `processed/`.
- On failure, the file is moved to `failed/`.
- Updates status in Redis.

---

## Stack

| Component         | Technology          |
|-------------------|---------------------|
| File Storage      | MinIO (S3 API)      |
| Messaging         | RabbitMQ            |
| OCR Engine        | Tesseract + Poppler |
| Web UI            | Flask               |
| Progress Tracking | Redis               |
| Database          | PostgreSQL          |
| Containerization  | Docker Compose      |

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

## Testing Locally

### 1. Upload Test Invoices
- Open your browser and go to: [http://localhost:5000](http://localhost:5000)
- Click **"Choose Files"** and select files from the `test_invoices` folder that is provided in the main project directory.
- Click the **"Upload"** button.
- You can confirm your uploaded files by visiting: [http://localhost:5000/status](http://localhost:5000/status)

---

### 2. Process All Files
- After uploading, click the **"Process All Files"** button on the homepage.
- The system will extract data, save it to the database, and move files to their respective folders (`processed/` or `failed/`).

---

### 3. Check Processing Results
- Visit: [http://localhost:5000/status](http://localhost:5000/status)
- All Failed files are moved to failed.
- There should be no more uploaded files, these are all processed and moved to the invoices page below.

---

### 4. View Invoices in the Database
- Visit: [http://localhost:5000/invoices](http://localhost:5000/invoices)
- See all successfully processed invoices.
- Download links are available for each associated file.

### Optional: 5. Create Your Own Invoices
- You can test the system with your own custom invoice PDFs.
- Just make sure your invoices include:
  - **Invoice:**
  - **Date:**
  - **Vendor:**
  - **Item list** with:
    - **Item**, **Qty**, **Unit Price**, **Total**

**Important Notes**  
The PDF-to-image processor used in this project does **not handle tables well** (e.g. grid-style tables with rows/columns).  
To ensure better text extraction accuracy:
- Replace tables with plain **text lists**
- Or use visual **borders** to separate items, but avoid complex grid layouts

**Invoice numbers must be unique**
  - Trying to process the same invoice twice with the same number will result in a failure (due to database constraints)
--- 

## Access

| Service          | URL                                                            |
| ---------------- | -------------------------------------------------------------- |
| Invoice Uploader | [http://localhost:5000](http://localhost:5000)                 |
| RabbitMQ UI      | [http://localhost:15672](http://localhost:15672) (guest/guest) |
| MinIO Console    | [http://localhost:9001](http://localhost:9001)                 |
| PostgreSQL       | localhost:5435 (via client)                                    |
| Redis            | localhost:6379 (via client)                                    |
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

## Resetting the DB and project
To reset the project and database run:

- docker-compose down -v
- docker-compose up -d

 This deletes all data in PostgreSQL and MinIO volumes.