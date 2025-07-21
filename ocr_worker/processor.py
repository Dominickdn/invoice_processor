import os
import tempfile
from botocore.exceptions import ClientError
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from io import BytesIO
from shared.s3_client import s3
from shared.redis_client import r

BUCKET = os.getenv("MINIO_BUCKET")


def download_from_s3(prefixed_key):
    obj = s3.get_object(Bucket=BUCKET, Key=prefixed_key)
    return BytesIO(obj["Body"].read())


def upload_to_s3(buffer, prefix, filename):
    s3.upload_fileobj(buffer, BUCKET, f"{prefix}{filename}")


def delete_from_s3(prefixed_key):
    s3.delete_object(Bucket=BUCKET, Key=prefixed_key)


def process_file(filename):
    key = f"{filename}"
    # Set status to processing
    r.set(key, "processing")
    try:
        body = download_from_s3(key)
    except ClientError as e:
        print(f"[ERROR] Cannot download {key}: {e}")
        return False, None

    try:
        ext = os.path.splitext(filename)[1].lower()
        text = ""

        if ext == ".pdf":
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=True
            ) as tmp_pdf:
                tmp_pdf.write(body.read())
                tmp_pdf.flush()
                images = convert_from_path(tmp_pdf.name)
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n\n"
        else:
            image = Image.open(body)
            text = pytesseract.image_to_string(image)

        print(f"[INFO] OCR complete for {filename}")
        print(f"[DEBUG] OCR Text:\n{text[:300]}...")

        return True, text

    except Exception as e:
        print(f"[ERROR] Processing failed for {filename}: {e}")
        # Set status to failed
        r.set(key, "failed")
        body.seek(0)
        upload_to_s3(body, "failed/", filename)
        delete_from_s3(key)
        return False, None
