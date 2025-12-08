# 請更新 .env 中的 MONGODB_URI

當前您的 `.env` 文件中的 MONGODB_URI 格式不完整。

## 正確的完整 URI

```
MONGODB_URI=mongodb+srv://admin:kiWKyFXU9LpCYGY5@cluster0.ktj8ev1.mongodb.net/stock_agent?retryWrites=true&w=majority
```

## 如何更新

1. 打開 `.env` 文件
2. 找到 `MONGODB_URI=...` 這一行
3. 替換為上面的完整 URI
4. 保存文件

## 驗證

更新後執行：
```bash
python -c "from database_manager import DatabaseManager; db = DatabaseManager()"
```

應該看到：
```
✅ [MongoDB] Connection Successful
```
