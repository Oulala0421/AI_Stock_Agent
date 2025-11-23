import requests
import time
import os

def send_telegram_chunked(message, token, chat_id):
    """
    Telegram 發送器 (含長訊息自動切分功能)
    限制：Telegram 單則上限 4096 字元
    """
    if not token or not chat_id: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 1. 如果訊息太長，切分發送
    max_length = 4000 # 預留一點緩衝
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    
    for i, msg_chunk in enumerate(messages):
        payload = {
            "chat_id": chat_id,
            "text": msg_chunk,
            "parse_mode": "Markdown" # 如果發送失敗，通常是 Markdown 語法錯誤
        }
        try:
            r = requests.post(url, json=payload)
            if r.status_code != 200:
                print(f"❌ TG 發送失敗 (第{i+1}段)")
                print(f"   Status Code: {r.status_code}")
                print(f"   Response: {r.text}")
                print(f"   Chat ID used: {chat_id}")
                print(f"💡 提示: 檢查 TG_CHAT_ID 是否正確（參考 docs/setup_guide.md）")
                # 嘗試用純文字重發 (Fallback)
                payload["parse_mode"] = None
                r2 = requests.post(url, json=payload)
                if r2.status_code == 200:
                    print(f"✅ TG 純文字模式重發成功 (第{i+1}段)")
            else:
                print(f"✅ TG 發送成功 (第{i+1}段)")
            
            time.sleep(1) # 避免發太快被擋
        except Exception as e:
            print(f"❌ TG 連線錯誤: {e}")

def send_line(message, token, user_id=None, group_id=None):
    """
    LINE 發送器 - 支援多種發送模式
    
    發送優先順序：
    1. **群組推送** (參數 group_id) - 優先
    2. **個人推送** (參數 user_id) - 次之
    3. **廣播** (都不提供) - 最後
    """
    if not token:
        print("⚠️ LINE_TOKEN 未設定，跳過 LINE 發送")
        return
    
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }
    
    # 長度限制處理
    message_text = message[:5000] if len(message) > 5000 else message
    
    # 判斷發送模式（優先順序：Group ID > User ID > Broadcast）
    if group_id and group_id.strip():
        # 模式 1: 群組推送 (Push to Group)
        url = "https://api.line.me/v2/bot/message/push"
        payload = {
            "to": group_id.strip(), 
            "messages": [{"type": "text", "text": message_text}]
        }
        mode_name = f"群組推送 (Group ID: {group_id[:10]}...)"
    elif user_id and user_id.strip():
        # 模式 2: 個人推送 (Push to User)
        url = "https://api.line.me/v2/bot/message/push"
        payload = {
            "to": user_id.strip(), 
            "messages": [{"type": "text", "text": message_text}]
        }
        mode_name = f"個人推送 (User ID: {user_id[:10]}...)"
    else:
        # 模式 3: 廣播 (Broadcast)
        url = "https://api.line.me/v2/bot/message/broadcast"
        payload = {
            "messages": [{"type": "text", "text": message_text}]
        }
        mode_name = "廣播 (Broadcast)"
    
    try: 
        r = requests.post(url, headers=headers, json=payload)
        
        if r.status_code == 200:
            print(f"✅ LINE 發送成功 ({mode_name})")
        elif r.status_code == 400:
            error_data = r.json() if r.text else {}
            error_msg = error_data.get('message', 'Unknown error')
            print(f"❌ LINE 發送失敗 ({mode_name})")
            print(f"   Status Code: 400 - Bad Request")
            print(f"   錯誤訊息: {error_msg}")
            if "Invalid user" in error_msg or "Invalid group" in error_msg:
                print(f"💡 提示: ID 無效")
                print(f"   - 群組 ID 請從 webhook 取得（執行 line_webhook_server.py）")
                print(f"   - 用戶 ID 格式應為 Uxxxxx...")
                print(f"   - 群組 ID 格式應為 Cxxxxx...")
            else:
                print(f"   Response: {r.text}")
        elif r.status_code == 401:
            print(f"❌ LINE 發送失敗 - 認證錯誤")
            print(f"   請檢查 LINE_TOKEN 是否正確")
        elif r.status_code == 403:
            print(f"❌ LINE 發送失敗 - 權限不足")
            print(f"   請確認 Bot 已加入目標群組，或檢查 Channel 權限設定")
        else:
            print(f"❌ LINE 發送失敗 ({mode_name})")
            print(f"   Status Code: {r.status_code}")
            print(f"   Response: {r.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ LINE 連線錯誤: {e}")
    except Exception as e:
        print(f"❌ LINE 發送異常: {e}")

# 為了相容 main.py，保留舊函式名稱並轉接
def send_telegram(message, token, chat_id):
    send_telegram_chunked(message, token, chat_id)