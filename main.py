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

# 正しいURLの住所
URL_BASE = f"https://jsonstorage.net/v1/json/{JSON_STORAGE_ID}?apiKey={JSON_STORAGE_KEY}"

# 外部データ置き場からチャット履歴を読み込む関数
def load_chat_history():
    try:
        response = requests.get(URL_BASE, timeout=5)
        # 正常に読み込めたらデータを返す
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            else:
                return []
        # まだデータが作られていなくて404エラーが出た場合は、自動で空のリストを作ってあげる
        elif response.status_code == 404:
            print("[SYSTEM] データボックスが未初期化のため、新規作成を行います。")
            create_first_chat_box([])
            return []
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
    return []

# 【超重要】一番最初にデータが存在しない場合、新規作成（POST）で箱を作る関数
def create_first_chat_box(messages):
    try:
        headers = {"Content-Type": "application/json"}
        # 404の時はPUTではなくPOSTで新しく箱を作る必要があるよ
        post_url = f"https://jsonstorage.net{JSON_STORAGE_KEY}"
        # あなたのIDを固定して新規作成するためのリクエスト
        payload = {
            "id": JSON_STORAGE_ID,
            "value": json.dumps(messages)
        }
        # もし上のやり方でダメな場合を考慮して、通常のURL_BASEへ空のリストをPOST送信する
        response = requests.post(URL_BASE, data=json.dumps(messages), headers=headers, timeout=5)
        print(f"[SYSTEM] 初期化POST結果: {response.status_code} | {response.text}")
    except Exception as e:
        print(f"初期化POSTエラー: {e}")

# 外部データ置き場にチャット履歴を上書き保存（PUT）する関数
def save_chat_history(messages):
    try:
        headers = {"Content-Type": "application/json"}
        response = requests.put(URL_BASE, data=json.dumps(messages), headers=headers, timeout=5)
        
        # もし上書き（PUT）が拒否されたら、まだ箱がない証拠なので新規作成（POST）に切り替える
        if response.status_code != 200:
            print(f"[SYSTEM] 上書き失敗({response.status_code})のため、新規作成(POST)を試みます。")
            response_post = requests.post(URL_BASE, data=json.dumps(messages), headers=headers, timeout=5)
            if response_post.status_code != 200:
                print(f"データ保存完全失敗: {response_post.text}")
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
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if user_ip and ',' in user_ip:
            user_ip = user_ip.split(',').strip()

        ADMIN_IP = "123.1.51.210" 
        is_admin = (user_ip == ADMIN_IP)

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
        
        if len(chat_messages) > 20:
            chat_messages.pop(0)
            
        save_chat_history(chat_messages)
            
    return jsonify({"status": "success"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
