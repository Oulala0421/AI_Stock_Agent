import requests
import time

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

def send_line(message, token, user_id=None):
    """
    LINE 發送器 - 支援個人推送 (push) 和群組廣播 (broadcast)
    
    使用方式:
    - 個人推送: 提供 user_id (LINE User ID)
    - 群組廣播: user_id 留空 (None or "")，系統自動使用 broadcast API
    
    注意：
    - broadcast 會發送給所有加入 Bot 的好友和群組
    - 如果您的 Bot 只加入一個群組，broadcast 就會發送到該群組
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
    
    # 判斷發送模式
    if user_id and user_id.strip():
        # 模式 1: 個人推送 (Push Message)
        url = "https://api.line.me/v2/bot/message/push"
        payload = {
            "to": user_id.strip(), 
            "messages": [{"type": "text", "text": message_text}]
        }
        mode_name = f"個人推送 (User ID: {user_id[:10]}...)"
    else:
        # 模式 2: 群組廣播 (Broadcast)
        url = "https://api.line.me/v2/bot/message/broadcast"
        payload = {
            "messages": [{"type": "text", "text": message_text}]
        }
        mode_name = "群組廣播 (Broadcast)"
    
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
            if "Invalid user" in error_msg:
                print(f"💡 提示: USER_ID 無效，建議改用廣播模式（將 LINE_USER_ID 留空）")
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