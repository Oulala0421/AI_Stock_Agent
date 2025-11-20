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

def send_line(message, token, user_id):
    if not token or not user_id: return
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    # LINE 也有長度限制，但通常較寬鬆，簡單處理
    payload = {"to": user_id, "messages": [{"type": "text", "text": message[:5000]}]}
    
    try: 
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200: 
            print(f"❌ LINE 發送失敗")
            print(f"   Status Code: {r.status_code}")
            print(f"   Response: {r.text}")
            print(f"   User ID used: {user_id}")
            print(f"💡 提示: 檢查 LINE_USER_ID 或改用 Broadcast（參考 docs/setup_guide.md）")
        else: print("✅ LINE 發送成功")
    except Exception as e: print(f"❌ LINE 錯誤: {e}")

# 為了相容 main.py，保留舊函式名稱並轉接
def send_telegram(message, token, chat_id):
    send_telegram_chunked(message, token, chat_id)