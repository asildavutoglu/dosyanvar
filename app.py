import os
import traceback

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from modules.evaluator import evaluate_resume
from modules.github_signals import fetch_github_signals
from modules.pdf_extract import extract_text_from_pdf

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB üst sınır


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/evaluate", methods=["POST"])
def evaluate():
    resume_file = request.files.get("resume")
    criteria = (request.form.get("criteria") or "").strip()
    github_username = (request.form.get("github_username") or "").strip()

    if not resume_file or resume_file.filename == "":
        return jsonify({"error": "Bir CV (PDF) yüklemen gerekiyor."}), 400
    if not criteria:
        return jsonify({"error": "Değerlendirilecek kriterleri veya iş ilanını yapıştırman gerekiyor."}), 400
    if not resume_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Şu an sadece PDF formatı destekleniyor."}), 400

    try:
        resume_text = extract_text_from_pdf(resume_file.read())
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"PDF okunamadı: {exc}"}), 400

    if not resume_text.strip():
        return jsonify({"error": "PDF içinden metin çıkarılamadı. Taranmış bir görüntü olabilir."}), 400

    github_data = None
    github_error = None
    if github_username:
        try:
            github_data = fetch_github_signals(github_username)
        except Exception as exc:  # noqa: BLE001
            github_error = str(exc)

    try:
        result = evaluate_resume(resume_text=resume_text, criteria=criteria, github_data=github_data)
    except Exception as exc:  # noqa: BLE001
        traceback.print_exc()
        return jsonify({"error": f"Değerlendirme sırasında hata oluştu: {exc}"}), 500

    if github_error:
        result["github_warning"] = github_error

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
