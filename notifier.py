import requests
import time
import os

def send_telegram_chunked(message, token, chat_id):
    """
    Telegram 發送器 (含長訊息自動切分功能 & 自動降級)
    限制：Telegram 單則上限 4096 字元
    """
    if not token or not chat_id: return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 1. 如果訊息太長，切分發送
    # 保守設定 3500 (避免 HTML/Markdown 標籤佔用長度導致爆掉)
    max_length = 3500 
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    
    for i, msg_chunk in enumerate(messages):
        # 預設嘗試 Markdown
        payload = {
            "chat_id": chat_id,
            "text": msg_chunk,
            "parse_mode": "Markdown" 
        }
        
        try:
            r = requests.post(url, json=payload, timeout=10)
            
            # 如果失敗 (通常是 400 Bad Request 語法錯誤)
            if r.status_code != 200:
                error_desc = r.json().get('description', '')
                print(f"⚠️ TG Markdown 發送失敗 (第{i+1}段): {error_desc}")
                
                # 自動降級為純文字 (Fallback)
                print(f"🔄 嘗試使用純文字重發...")
                payload["parse_mode"] = None
                r2 = requests.post(url, json=payload, timeout=10)
                
                if r2.status_code == 200:
                    print(f"✅ TG 純文字模式重發成功 (第{i+1}段)")
                else:
                    print(f"❌ TG 發送最終失敗 (第{i+1}段)")
                    print(f"   Response: {r2.text}")
            else:
                print(f"✅ TG 發送成功 (第{i+1}段)")
            
            time.sleep(1) # 避免 Rate Limit
            
        except Exception as e:
            print(f"❌ TG 連線錯誤: {e}")

def send_line(message, token, user_id=None, group_id=None):
    """
    LINE 發送器 - 支援多種發送模式和訊息自動分段
    
    發送優先順序：
    1. **群組推送** (參數 group_id) - 優先
    2. **個人推送** (參數 user_id) - 次之
    3. **廣播** (都不提供) - 最後
    
    限制：LINE 單則訊息上限 5000 字元
    """
    if not token:
        print("⚠️ LINE_TOKEN 未設定，跳過 LINE 發送")
        return
    
    headers = {
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {token}"
    }
    
    # 訊息分段處理 (LINE 限制 5000 字元,預留緩衝設 4800)
    max_length = 4800
    message_chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    
    # 判斷發送模式
    if group_id and group_id.strip():
        target_id = group_id.strip()
        url = "https://api.line.me/v2/bot/message/push"
        mode_name = f"群組推送 (Group ID: {group_id[:10]}...)"
    elif user_id and user_id.strip():
        target_id = user_id.strip()
        url = "https://api.line.me/v2/bot/message/push"
        mode_name = f"個人推送 (User ID: {user_id[:10]}...)"
    else:
        target_id = None
        url = "https://api.line.me/v2/bot/message/broadcast"
        mode_name = "廣播 (Broadcast)"
    
    # 逐段發送
    for i, chunk in enumerate(message_chunks):
        if target_id:
            payload = {
                "to": target_id, 
                "messages": [{"type": "text", "text": chunk}]
            }
        else:
            payload = {
                "messages": [{"type": "text", "text": chunk}]
            }
        
        try: 
            r = requests.post(url, headers=headers, json=payload)
            
            if r.status_code == 200:
                if len(message_chunks) > 1:
                    print(f"✅ LINE 發送成功 ({mode_name}) - 第{i+1}/{len(message_chunks)}段")
                else:
                    print(f"✅ LINE 發送成功 ({mode_name})")
            elif r.status_code == 400:
                error_data = r.json() if r.text else {}
                error_msg = error_data.get('message', 'Unknown error')
                print(f"❌ LINE 發送失敗 ({mode_name}) - 第{i+1}段")
                print(f"   Status Code: 400 - Bad Request")
                print(f"   錯誤訊息: {error_msg}")
                if "Invalid user" in error_msg or "Invalid group" in error_msg:
                    print(f"💡 提示: ID 無效")
                    print(f"   - 群組 ID 請從 webhook 取得（執行 line_webhook_server.py）")
                    print(f"   - 用戶 ID 格式應為 Uxxxxx...")
                    print(f"   - 群組 ID 格式應為 Cxxxxx...")
                elif "Length must be between" in error_msg:
                    print(f"💡 提示: 訊息長度超過限制")
                    print(f"   - 當前段落長度: {len(chunk)} 字元")
                    print(f"   - LINE 限制: 5000 字元")
                else:
                    print(f"   Response: {r.text}")
                return  # 某段失敗就停止後續發送
            elif r.status_code == 401:
                print(f"❌ LINE 發送失敗 - 認證錯誤")
                print(f"   請檢查 LINE_TOKEN 是否正確")
                return
            elif r.status_code == 403:
                print(f"❌ LINE 發送失敗 - 權限不足")
                print(f"   請確認 Bot 已加入目標群組，或檢查 Channel 權限設定")
                return
            else:
                print(f"❌ LINE 發送失敗 ({mode_name}) - 第{i+1}段")
                print(f"   Status Code: {r.status_code}")
                print(f"   Response: {r.text}")
                return
            
            # 避免發太快被限流
            if i < len(message_chunks) - 1:
                time.sleep(1)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ LINE 連線錯誤 (第{i+1}段): {e}")
            return
        except Exception as e:
            print(f"❌ LINE 發送異常 (第{i+1}段): {e}")
            return

# 為了相容 main.py，保留舊函式名稱並轉接
def send_telegram(message, token, chat_id):
    send_telegram_chunked(message, token, chat_id)

def send_private_line(message, token, user_id):
    """
    專門用於發送私人通知的輔助函式
    """
    if not user_id:
        print("⚠️ 無法發送私人訊息: USER_ID 未設定")
        return
    
    print(f"🤫 發送私人通知給 {user_id[:6]}...")
    send_line(message, token, user_id=user_id)