import os
import json
from datetime import datetime
import pytz
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# ファイルの保存先パス（Renderの永続ディスクを使う場合は /data/chat_history.json にするよ）
HISTORY_FILE = "chat_history.json"

# ファイルからチャット履歴を読み込む関数
def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# ファイルにチャット履歴を保存する関数
def save_chat_history(messages):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"ファイル保存エラー: {e}")

@app.route("/", methods=["GET"])
def index():
    jst = pytz.timezone('Asia/Tokyo')
    shizuoka_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")

    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return render_template_string(html_content, current_time=shizuoka_time)

@app.route("/get_messages", methods=["GET"])
def get_messages():
    # 常にファイルから最新のデータを読み込んで返す
    return jsonify(load_chat_history())

@app.route("/send_message", methods=["POST"])
def send_message():
    user_name = request.form.get("username", "名無しさん")
    if not user_name:
        user_name = "名無しさん"
    message = request.form.get("message", "").strip()
    
    if message:
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',')[0].strip()

        ADMIN_IP = "123.1.51.210" 
        is_admin = (user_ip == ADMIN_IP)

        jst = pytz.timezone('Asia/Tokyo')
        now_str = datetime.now(jst).strftime("%H:%M:%S")
        
        # 現在の履歴をファイルから読み出す
        chat_messages = load_chat_history()
        
        chat_messages.append({
            "name": user_name, 
            "text": message, 
            "time": now_str,
            "is_admin": is_admin
        })
        
        if len(chat_messages) > 20:
            chat_messages.pop(0)
            
        # 変更した履歴をファイルに保存する
        save_chat_history(chat_messages)
            
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
