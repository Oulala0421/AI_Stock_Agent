"""
LINE Webhook Server - 用於取得群組 ID

功能：
1. 接收 LINE Platform 發送的 Webhook 事件
2. 解析並顯示群組 ID (groupId)
3. 可選：自動保存 Group ID 到 .env 檔案

使用方式：
1. 執行此伺服器: python line_webhook_server.py
2. 使用 ngrok 暴露: ngrok http 5000
3. 將 ngrok URL 設定到 LINE Developers Console
4. 在 LINE 群組中發送訊息
5. 查看終端機輸出的群組 ID
"""

from flask import Flask, request, abort
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

# LINE Channel Secret (用於驗證 Webhook 簽名)
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')

def verify_signature(body, signature):
    """
    驗證 Webhook 請求的簽名（可選）
    詳見：https://developers.line.biz/en/docs/messaging-api/receiving-messages/#verify-signature
    """
    if not CHANNEL_SECRET:
        print("⚠️ LINE_CHANNEL_SECRET 未設定，跳過簽名驗證")
        return True
    
    import hmac
    import hashlib
    import base64
    
    hash = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    expected_signature = base64.b64encode(hash).decode('utf-8')
    return signature == expected_signature

@app.route("/webhook", methods=['POST'])
def webhook():
    """
    LINE Webhook 端點
    文件：https://developers.line.biz/en/reference/messaging-api/#message-event
    """
    # 取得簽名（用於驗證請求來自 LINE）
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    # 驗證簽名（生產環境建議啟用）
    # if not verify_signature(body, signature):
    #     print("❌ 簽名驗證失敗")
    #     abort(400)
    
    try:
        # 解析 JSON
        data = json.loads(body)
        
        print("\n" + "="*60)
        print("📩 收到 Webhook 事件")
        print("="*60)
        
        # 處理每個事件
        for event in data.get('events', []):
            event_type = event.get('type')
            source = event.get('source', {})
            source_type = source.get('type')
            
            print(f"\n事件類型: {event_type}")
            print(f"來源類型: {source_type}")
            
            # 重點：取得 Group ID
            if source_type == 'group':
                group_id = source.get('groupId')
                user_id = source.get('userId', '未知')
                
                print("\n" + "🎯" * 20)
                print(f"✅ 找到群組 ID！")
                print(f"\n群組 ID: {group_id}")
                print(f"用戶 ID: {user_id}")
                
                # 如果是訊息事件，顯示訊息內容
                if event_type == 'message':
                    message = event.get('message', {})
                    message_type = message.get('type')
                    
                    if message_type == 'text':
                        text = message.get('text')
                        print(f"訊息內容: {text}")
                
                print("\n" + "-"*60)
                print("📝 請將以下內容加入 .env 檔案：")
                print(f"LINE_GROUP_ID={group_id}")
                print("-"*60)
                print("🎯" * 20 + "\n")
                
                # 可選：自動追加到 .env 檔案
                # with open('.env', 'a') as f:
                #     f.write(f"\nLINE_GROUP_ID={group_id}\n")
                
            elif source_type == 'user':
                user_id = source.get('userId')
                print(f"\n這是一對一訊息（User ID: {user_id}）")
                print("💡 要取得群組 ID，請在群組中發送訊息")
            
            elif source_type == 'room':
                room_id = source.get('roomId')
                print(f"\n這是多人聊天室（Room ID: {room_id}）")
            
            # 顯示完整事件（除錯用）
            print(f"\n完整事件 JSON:")
            print(json.dumps(event, indent=2, ensure_ascii=False))
            print("="*60)
        
        return 'OK', 200
        
    except Exception as e:
        print(f"❌ 處理 Webhook 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 'Error', 500

@app.route("/")
def index():
    """健康檢查端點"""
    return """
    <h1>LINE Webhook Server 運行中</h1>
    <p>Webhook 端點: <code>/webhook</code></p>
    <p>請將此 URL 設定到 LINE Developers Console</p>
    <hr>
    <h2>操作步驟：</h2>
    <ol>
        <li>在 LINE 群組中加入您的 Bot</li>
        <li>在群組中發送任意訊息</li>
        <li>查看終端機輸出的群組 ID</li>
        <li>將群組 ID 複製到 .env 檔案</li>
    </ol>
    """

@app.route("/health")
def health():
    """健康檢查（用於雲端部署）"""
    return {"status": "healthy"}, 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 LINE Webhook Server 啟動中...")
    print("="*60)
    print("\n監聽端口: 5000")
    print("Webhook 路徑: /webhook")
    print("\n請執行以下步驟：")
    print("1. 開啟新終端機執行: ngrok http 5000")
    print("2. 複製 ngrok 提供的 HTTPS URL")
    print("3. 在 LINE Developers 設定 Webhook URL: https://YOUR_NGROK_URL/webhook")
    print("4. 在 LINE 群組中發送訊息")
    print("5. 查看下方輸出的群組 ID\n")
    print("="*60 + "\n")
    
    # 啟動 Flask 伺服器
    app.run(host='0.0.0.0', port=5000, debug=True)
