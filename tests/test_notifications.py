"""
通知系統連線測試腳本

測試 Gemini API、Telegram 和 LINE 的連線狀態和設定正確性。
"""

import os
from dotenv import load_dotenv
import requests
from google import genai

# 載入環境變數
load_dotenv()

def test_gemini_api():
    """測試 Gemini API 連線"""
    print("\n🧪 測試 Gemini API...")
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 找不到 GEMINI_API_KEY")
        return False
    
    print(f"✓ API Key 已設定（前10字元：{api_key[:10]}...）")
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents='請用一句話回應：測試成功'
        )
        print(f"✅ Gemini API 連線成功")
        print(f"   回應: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini API 連線失敗")
        print(f"   錯誤類型: {type(e).__name__}")
        print(f"   錯誤訊息: {str(e)}")
        return False

def test_telegram():
    """測試 Telegram Bot 連線"""
    print("\n🧪 測試 Telegram...")
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    
    if not token:
        print("❌ 找不到 TG_TOKEN")
        return False
    if not chat_id:
        print("❌ 找不到 TG_CHAT_ID")
        return False
    
    print(f"✓ Token 已設定（前10字元：{token[:10]}...）")
    print(f"✓ Chat ID: {chat_id}")
    
    # 測試 getMe（檢查 Token 有效性）
    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        r = requests.get(url)
        if r.status_code == 200:
            bot_info = r.json()['result']
            print(f"✓ Bot 名稱: @{bot_info['username']}")
        else:
            print(f"❌ Token 無效: {r.text}")
            return False
    except Exception as e:
        print(f"❌ 無法連線到 Telegram API: {e}")
        return False
    
    # 發送測試訊息
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "✅ AI Stock Agent 通知測試成功！\n這是一則測試訊息。"
        }
        r = requests.post(url, json=payload)
        
        if r.status_code == 200:
            print(f"✅ Telegram 測試訊息發送成功")
            return True
        else:
            print(f"❌ Telegram 發送失敗")
            print(f"   Status Code: {r.status_code}")
            print(f"   Response: {r.text}")
            print(f"\n💡 提示：")
            print(f"   1. 確認已傳送訊息給 Bot 啟動對話")
            print(f"   2. 檢查 Chat ID 是否正確（參考 docs/setup_guide.md）")
            return False
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False

def test_line():
    """測試 LINE Messaging API"""
    print("\n🧪 測試 LINE...")
    token = os.getenv("LINE_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    
    if not token:
        print("❌ 找不到 LINE_TOKEN")
        return False
    
    print(f"✓ Token 已設定（前10字元：{token[:10]}...）")
    
    # 如果沒有 User ID，提示使用 Broadcast
    if not user_id:
        print("⚠️ 找不到 LINE_USER_ID")
        print("💡 建議改用 Broadcast API（推送給所有好友）")
        print("   參考 docs/setup_guide.md 的「推薦方案：改用 Broadcast」")
        return False
    
    print(f"✓ User ID: {user_id}")
    
    # 發送測試訊息
    try:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        payload = {
            "to": user_id,
            "messages": [{
                "type": "text",
                "text": "✅ AI Stock Agent 通知測試成功！\n這是一則測試訊息。"
            }]
        }
        
        r = requests.post(url, headers=headers, json=payload)
        
        if r.status_code == 200:
            print(f"✅ LINE 測試訊息發送成功")
            return True
        else:
            print(f"❌ LINE 發送失敗")
            print(f"   Status Code: {r.status_code}")
            print(f"   Response: {r.text}")
            print(f"\n💡 提示：")
            print(f"   1. 檢查 User ID 格式是否正確")
            print(f"   2. 或改用 Broadcast API（參考設定指南）")
            return False
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False

def main():
    print("=" * 60)
    print("🔬 AI Stock Agent 通知系統測試")
    print("=" * 60)
    
    results = {
        "Gemini API": test_gemini_api(),
        "Telegram": test_telegram(),
        "LINE": test_line()
    }
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    for service, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{service:15} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有測試通過！系統配置正確。")
        print("\n下一步：")
        print("1. 執行本地 Dry Run 測試: python main.py --mode post_market --dry-run")
        print("2. 更新 GitHub Secrets（參考 docs/setup_guide.md）")
        print("3. 手動執行 GitHub Actions 測試")
    else:
        print("\n⚠️ 部分測試失敗，請檢查設定。")
        print("\n參考文件: docs/setup_guide.md")
    
    return all_passed

if __name__ == "__main__":
    main()
