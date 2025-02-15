from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import qrcode
import io
import base64
import threading
import time
import random
import string
import pandas as pd
import os



app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

EXCEL_FILE = "students.xlsx"

# التحقق من وجود ملف Excel أو إنشائه
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["ID", "Name", "Scanned QR Code"])
    df.to_excel(EXCEL_FILE, index=False)

# دالة توليد QR Code مع رابط للمسح عبر الهاتف
def generate_qr():
    while True:
        random_data = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        scan_url = f"http://192.168.1.9:5000/scan/{random_data}"  # استبدل 192.168.1.10 بـ IP جهازك

        qr = qrcode.make(scan_url)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        socketio.emit('update_qr', f"data:image/png;base64,{qr_base64}")

        time.sleep(2)  # تحديث كل ثانيتين

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan/<qr_data>", methods=["GET", "POST"])
def scan(qr_data):
    if request.method == "POST":
        student_id = request.form["student_id"]
        student_name = request.form["student_name"]

        # حفظ البيانات في ملف Excel
        df = pd.read_excel(EXCEL_FILE)
        new_data = pd.DataFrame({"ID": [student_id], "Name": [student_name], "Scanned QR Code": [qr_data]})
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_excel(EXCEL_FILE, index=False)

        return redirect(url_for("success"))

    return render_template("scan.html", qr_data=qr_data)

@app.route("/success")
def success():
    return "تم حفظ البيانات بنجاح! ✅"

if __name__ == "__main__":
    threading.Thread(target=generate_qr, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
