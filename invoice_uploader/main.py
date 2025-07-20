import boto3
import os
from enqueue_files import enqueue_files
from ensure_bucket_exists import ensure_bucket_exists
from flask import Flask, render_template, request, redirect, flash, url_for
from db.query import get_invoices_with_items
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)
app.secret_key = "supersecret"

# S3 config
s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
)

BUCKET = os.getenv("MINIO_BUCKET")
UPLOAD_PREFIX = "process/"

ensure_bucket_exists(BUCKET)


@app.route("/")
def index():
    # List all files in the process/ prefix
    objects = s3.list_objects_v2(Bucket=BUCKET, Prefix=UPLOAD_PREFIX)
    files = []
    for obj in objects.get("Contents", []):
        key = obj["Key"]
        if not key.endswith("/"):
            files.append(key.replace(UPLOAD_PREFIX, ""))  # strip prefix
    return render_template("index.html", files=files)


@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        flash("No files part")
        return redirect(url_for("index"))

    uploaded_files = request.files.getlist("files")
    if not uploaded_files:
        flash("No selected files")
        return redirect(url_for("index"))

    for file in uploaded_files:
        if file.filename == "":
            continue
        filename = secure_filename(file.filename)
        s3.upload_fileobj(file, BUCKET, f"{UPLOAD_PREFIX}{filename}")
        flash(f"Uploaded: {filename}")
    return redirect(url_for("index"))


@app.route("/status")
def status():
    def list_files(prefix):
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        contents = response.get("Contents", [])
        return [
            obj["Key"].replace(prefix, "")
            for obj in contents
            if not obj["Key"].endswith("/")
        ]

    processed_files = list_files("processed/")
    failed_files = list_files("failed/")
    return render_template(
        "status.html", processed=processed_files, failed=failed_files
    )


@app.route("/delete", methods=["POST"])
def delete():
    folder = request.form["folder"]
    filename = request.form["filename"]

    if folder not in ["processed", "failed"]:
        flash("Invalid folder.")
        return redirect(url_for("status"))

    key = f"{folder}/{filename}"

    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        flash(f"Deleted {filename} from {folder}/")
    except Exception as e:
        flash(f"Error deleting file: {str(e)}")

    return redirect(url_for("status"))


@app.route("/enqueue", methods=["POST"])
def enqueue():
    enqueue_files()
    flash("All files enqueued")
    return redirect(url_for("index"))


@app.route("/invoices")
def invoices():
    per_page = 20
    page = int(request.args.get("page", 1))  # Default to page 1
    offset = (page - 1) * per_page

    all_invoices = get_invoices_with_items(limit=per_page, offset=offset)
    return render_template("invoices.html", invoices=all_invoices, page=page)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)
