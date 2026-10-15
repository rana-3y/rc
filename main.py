import os
from datetime import datetime
import pytz
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# チャットのメッセージを保存するリスト
chat_messages = []

@app.route("/", methods=["GET"])
def index():
    jst = pytz.timezone('Asia/Tokyo')
    shizuoka_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")

    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return render_template_string(html_content, current_time=shizuoka_time)

@app.route("/get_messages", methods=["GET"])
def get_messages():
    return jsonify(chat_messages)

@app.route("/send_message", methods=["POST"])
def send_message():
    user_name = request.form.get("username", "名無しさん")
    if not user_name:
        user_name = "名無しさん"
    message = request.form.get("message", "").strip()
    
    if message:
        # 送信者のIPアドレスを取得（Renderなどのプロキシ環境に対応）
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',')[0].strip()

        # 【重要】
        ADMIN_IP = "123.1.51.210" 

        # IPアドレスが一致したら管理者フラグをTrueにする
        is_admin = (user_ip == ADMIN_IP)

        jst = pytz.timezone('Asia/Tokyo')
        now_str = datetime.now(jst).strftime("%H:%M:%S")
        
        chat_messages.append({
            "name": user_name, 
            "text": message, 
            "time": now_str,
            "is_admin": is_admin # 管理者かどうかの情報を追加
        })
        
        if len(chat_messages) > 20:
            chat_messages.pop(0)
            
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

