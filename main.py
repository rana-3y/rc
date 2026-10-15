import os
import json
from datetime import datetime
import pytz
import requests  # 外部のデータ置き場と通信するために使うよ
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# =========================================================
# 【重要】JsonStorageの情報をここにセットしたよ！
# =========================================================
JSON_STORAGE_ID = "95433469-a539-4b07-93d8-3310579dfe3a"
JSON_STORAGE_KEY = "a34426ab-e063-4ba9-8b91-943cdad7b694"
# =========================================================

URL = f"https://jsonstorage.net{JSON_STORAGE_ID}?apiKey={JSON_STORAGE_KEY}"

# 外部データ置き場からチャット履歴を読み込む関数
def load_chat_history():
    try:
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # データが正しいリスト形式ならそのまま返す
            if isinstance(data, list):
                return data
            else:
                # もし中身が空っぽ（{}など）なら、自動で空のリストにして初期化保存するよ！
                save_chat_history([])
                return []
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
    return []

# 外部データ置き場にチャット履歴を保存する関数
def save_chat_history(messages):
    try:
        headers = {"Content-Type": "application/json"}
        # 確実に正しいJSONデータの形にして上書き保存する
        response = requests.put(URL, data=json.dumps(messages), headers=headers, timeout=5)
        if response.status_code != 200:
            print(f"データ保存失敗: {response.text}")
    except Exception as e:
        print(f"データ保存エラー: {e}")

@app.route("/", methods=["GET"])
def index():
    jst = pytz.timezone('Asia/Tokyo')
    shizuoka_time = datetime.now(jst).strftime("%Y年%m月%d日 %H:%M:%S")

    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    return render_template_string(html_content, current_time=shizuoka_time)

@app.route("/get_messages", methods=["GET"])
def get_messages():
    return jsonify(load_chat_history())

@app.route("/send_message", methods=["POST"])
def send_message():
    user_name = request.form.get("username", "名無しさん")
    if not user_name:
        user_name = "名無しさん"
    message = request.form.get("message", "").strip()
    
    if message:
        # 送信者の本当のIPアドレスを取得
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',').strip()

        # 君のIPアドレス
        ADMIN_IP = "123.1.51.210" 
        is_admin = (user_ip == ADMIN_IP)

        # RenderのログにだけIPを出力する（安全）
        print(f"[ADMIN CHECK] IP: {user_ip} | Name: {user_name} | AdminMatch: {is_admin}")

        jst = pytz.timezone('Asia/Tokyo')
        now_str = datetime.now(jst).strftime("%H:%M:%S")
        
        chat_messages = load_chat_history()
        
        chat_messages.append({
            "name": user_name, 
            "text": message, 
            "time": now_str,
            "is_admin": is_admin
        })
        
        # 最新の20件だけ残す
        if len(chat_messages) > 20:
            chat_messages.pop(0)
            
        save_chat_history(chat_messages)
            
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
