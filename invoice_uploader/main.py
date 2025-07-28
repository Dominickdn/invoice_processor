import os
from enqueue_files import enqueue_files
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    flash,
    url_for,
    send_file,
)
from db.query import get_invoices_with_items
from dotenv import load_dotenv
from utils.redis_client import r
from utils.s3_client import (
    download_from_s3,
    upload_to_s3,
    delete_from_s3,
    list_files_in_folder,
    ensure_bucket_exists,
)
from werkzeug.utils import secure_filename

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


BUCKET = os.getenv("MINIO_BUCKET")
UPLOAD_PREFIX = "process/"

ensure_bucket_exists(BUCKET)


@app.route("/")
def index():
    files = list_files_in_folder(UPLOAD_PREFIX)
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
        upload_to_s3(file, UPLOAD_PREFIX, filename)
        flash(f"Uploaded: {filename}")
    return redirect(url_for("index"))


@app.route("/progress")
def progress():
    keys = r.keys("process/*")
    total = len(keys)
    status_counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0}

    for key in keys:
        status = r.get(key)
        if status in status_counts:
            status_counts[status] += 1

    return {
        "total": total,
        "queued": status_counts["queued"],
        "processing": status_counts["processing"],
        "completed": status_counts["completed"],
        "failed": status_counts["failed"],
    }


@app.route("/reset-progress", methods=["POST"])
def reset_progress():
    for key in r.scan_iter("process/*"):
        r.delete(key)
    return "", 204


@app.route("/status")
def status():
    process_files = list_files_in_folder("process/")
    failed_files = list_files_in_folder("failed/")
    return render_template(
        "status.html", process=process_files, failed=failed_files
    )


@app.route("/delete", methods=["POST"])
def delete():
    folder = request.form["folder"]
    filename = request.form["filename"]

    allowed_folders = ["process", "failed", "processed"]
    if folder not in allowed_folders:
        flash("Invalid folder.")
        return redirect(url_for("status"))

    key = f"{folder}/{filename}"

    try:
        delete_from_s3(key)
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
    per_page = 10
    page = int(request.args.get("page", 1))
    offset = (page - 1) * per_page

    invoices_with_items = get_invoices_with_items(
        limit=per_page + 1, offset=offset
    )

    has_next = len(invoices_with_items) > per_page
    invoices_to_display = invoices_with_items[:per_page]
    return render_template(
        "invoices.html",
        invoices=invoices_to_display,
        page=page,
        has_next=has_next,
    )


@app.route("/download/<path:filename>")
def download_file(filename):
    prefixed_key = filename
    try:
        file_stream = download_from_s3(prefixed_key)
        return send_file(
            file_stream, download_name=filename, as_attachment=False
        )
    except Exception as e:
        return f"Error retrieving file: {str(e)}", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
