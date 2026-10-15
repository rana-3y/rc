import os
from datetime import datetime
import pytz
from flask import Flask, render_template_string, request, redirect, jsonify

app = Flask(__name__)

# チャットのメッセージを保存するリスト
chat_messages = []

@app.route("/", methods=["GET"])
def index():
    # 静岡の現在時刻を取得
    jst = pytz.timezone('Asia/Tokyo')
    shizuoka_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")

    # index.htmlを読み込んで画面を表示する
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return render_template_string(html_content, current_time=shizuoka_time)

# 【追加】新着メッセージをJavaScriptに送るためのルート
@app.route("/get_messages", methods=["GET"])
def get_messages():
    return jsonify(chat_messages)

# 【追加】メッセージを投稿するためのルート（画面遷移させない）
@app.route("/send_message", methods=["POST"])
def send_message():
    user_name = request.form.get("username", "名無しさん")
    if not user_name:
        user_name = "名無しさん"
    message = request.form.get("message", "").strip()
    
    if message:
        jst = pytz.timezone('Asia/Tokyo')
        now_str = datetime.now(jst).strftime("%H:%M:%S")
        chat_messages.append({"name": user_name, "text": message, "time": now_str})
        
        if len(chat_messages) > 20:
            chat_messages.pop(0)
            
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("SERVER_PORT", 8080))
    app.run(host="0.0.0.0", port=port)
