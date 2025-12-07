#!/usr/bin/env python3
"""測試 LINE 訊息發送功能"""

import os
from dotenv import load_dotenv
from notifier import send_line
from config import Config
import requests

# 載入環境變數
load_dotenv()

def test_line_token():
    """測試LINE TOKEN是否有效"""
    token = Config.get('LINE_TOKEN')
    
    print("=" * 60)
    print("🔍 LINE TOKEN 檢測")
    print("=" * 60)
    
    if not token:
        print("❌ LINE_TOKEN 未設定")
        return False
    
    print(f"✅ LINE_TOKEN 已載入: {token[:20]}...")
    
    # 測試 token 有效性
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 檢查 bot info
    try:
        r = requests.get("https://api.line.me/v2/bot/info", headers=headers)
        if r.status_code == 200:
            bot_info = r.json()
            print(f"✅ Bot 資訊正確:")
            print(f"   Bot Name: {bot_info.get('displayName', 'N/A')}")
            print(f"   Bot ID: {bot_info.get('userId', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Token 驗證失敗: {r.status_code}")
            print(f"   Response: {r.text}")
            return False
    except Exception as e:
        print(f"❌ Token 驗證錯誤: {e}")
        return False

def test_line_send():
    """測試 LINE 發送功能"""
    
    print("\n" + "=" * 60)
    print("📤 LINE 發送測試")
    print("=" * 60)
    
    token = Config.get('LINE_TOKEN')
    user_id = Config.get('LINE_USER_ID')
    group_id = Config.get('LINE_GROUP_ID')
    
    print(f"Token: {token[:20] if token else 'EMPTY'}...")
    print(f"User ID: {user_id}")
    print(f"Group ID: {group_id}")
    
    test_message = "🧪 LINE 發送測試\n這是一則測試訊息，請忽略。"
    
    # 測試群組發送
    if group_id:
        print("\n📌 測試群組發送...")
        send_line(test_message, token, user_id=None, group_id=group_id)
    else:
        print("\n⚠️ 未設定 GROUP_ID，跳過群組測試")
    
    # 測試個人發送
    if user_id:
        print("\n📌 測試個人發送...")
        send_line(test_message, token, user_id=user_id, group_id=None)
    else:
        print("\n⚠️ 未設定 USER_ID，跳過個人測試")

def check_bot_in_group():
    """檢查 Bot 是否在群組中"""
    print("\n" + "=" * 60)
    print("👥 群組成員檢查")
    print("=" * 60)
    
    token = Config.get('LINE_TOKEN')
    group_id = Config.get('LINE_GROUP_ID')
    
    if not group_id:
        print("⚠️ 未設定 LINE_GROUP_ID")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 嘗試獲取群組摘要
    try:
        url = f"https://api.line.me/v2/bot/group/{group_id}/summary"
        r = requests.get(url, headers=headers)
        
        if r.status_code == 200:
            info = r.json()
            print(f"✅ 群組資訊:")
            print(f"   群組名稱: {info.get('groupName', 'N/A')}")
            print(f"   成員數: {info.get('count', 'N/A')}")
        elif r.status_code == 403:
            print("❌ Bot 可能未加入該群組，或沒有權限")
            print("💡 請確認:")
            print("   1. Bot 已被加入群組")
            print("   2. Bot 未被封鎖")
        else:
            print(f"❌ 查詢失敗: {r.status_code}")
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ 查詢錯誤: {e}")

if __name__ == "__main__":
    print("🚀 開始 LINE 通知診斷測試\n")
    
    # Step 1: 檢查 Token
    token_valid = test_line_token()
    
    if not token_valid:
        print("\n❌ TOKEN 無效，無法繼續測試")
        exit(1)
    
    # Step 2: 檢查群組
    check_bot_in_group()
    
    # Step 3: 測試發送
    test_line_send()
    
    print("\n" + "=" * 60)
    print("✅ 診斷測試完成")
    print("=" * 60)
