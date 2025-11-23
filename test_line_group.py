"""
LINE 群組發送測試腳本

測試是否能成功發送訊息到特定 LINE 群組
"""

import os
from dotenv import load_dotenv
from notifier import send_line
from datetime import datetime

load_dotenv()

def test_line_group_message():
    print("\n" + "="*60)
    print("🧪 LINE 群組發送測試")
    print("="*60)
    
    # 檢查環境變數
    line_token = os.getenv('LINE_TOKEN')
    line_group_id = os.getenv('LINE_GROUP_ID')
    line_user_id = os.getenv('LINE_USER_ID')
    
    print("\n📋 環境變數檢查：")
    print(f"  LINE_TOKEN: {'✅ 已設定' if line_token else '❌ 未設定'}")
    print(f"  LINE_GROUP_ID: {'✅ 已設定 (' + line_group_id[:15] + '...)' if line_group_id else '⚠️ 未設定（將使用廣播模式）'}")
    print(f"  LINE_USER_ID: {'✅ 已設定' if line_user_id else '⚠️ 未設定'}")
    
    if not line_token:
        print("\n❌ 錯誤：LINE_TOKEN 未設定")
        print("請在 .env 檔案中設定 LINE_TOKEN")
        return
    
    # 建立測試訊息
    test_message = f"""
🧪 【LINE 群組發送測試】

✅ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果您在 LINE 群組中看到這則訊息，表示：
1. ✅ Bot 已成功加入群組
2. ✅ 群組 ID 設定正確
3. ✅ LINE_TOKEN 有效
4. ✅ 發送功能正常運作

接下來可以開始使用 AI Stock Agent 的自動通知功能！

---
💡 提示：若要停止接收測試訊息，請執行正式版本的 main.py
""".strip()
    
    print("\n📤 準備發送測試訊息...")
    print(f"訊息長度: {len(test_message)} 字元")
    
    # 顯示將使用的模式
    if line_group_id:
        print(f"\n🎯 模式: 群組推送 (Group ID: {line_group_id[:15]}...)")
    elif line_user_id:
        print(f"\n🎯 模式: 個人推送 (User ID: {line_user_id[:10]}...)")
    else:
        print(f"\n🎯 模式: 廣播 (Broadcast)")
    
    print("\n" + "-"*60)
    
    # 發送測試訊息
    send_line(test_message, line_token, line_user_id)
    
    print("\n" + "="*60)
    print("📝 測試完成說明：")
    print("="*60)
    
    if line_group_id:
        print("\n✅ 如果看到「LINE 發送成功 (群組推送...)」")
        print("   → 請到 LINE 群組檢查是否收到訊息")
        print("\n❌ 如果看到錯誤訊息：")
        print("   → 400 Bad Request: 群組 ID 可能錯誤，請重新從 webhook 取得")
        print("   → 403 Forbidden: Bot 可能未加入該群組")
        print("   → 401 Unauthorized: LINE_TOKEN 無效")
    else:
        print("\n⚠️ 未設定 LINE_GROUP_ID")
        print("\n建議步驟：")
        print("1. 執行: python line_webhook_server.py")
        print("2. 開啟新終端機執行: ngrok http 5000")
        print("3. 將 ngrok URL 設定到 LINE Developers")
        print("4. 在 LINE 群組中發送任意訊息")
        print("5. 複製顯示的群組 ID 到 .env 檔案")
        print("\n詳細教學請參考: docs/LINE_WEBHOOK_SETUP.md")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_line_group_message()
