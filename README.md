# 台股上班偷看盤（桌面版）

這個專案已改為 **Python Tkinter 視窗化介面**，不再依賴 HTML 頁面看盤。

## 功能

- 自訂視窗化介面（桌面 App）
- 每 5 秒自動更新台股報價
- 可新增 / 移除四碼股票代號
- 本地保存追蹤清單（`watchlist.json`）
- 修正四碼代號查不到資料問題：同時查詢 `tse`（上市）與 `otc`（上櫃）通道

## 使用方式

1. 確認本機有 Python 3（建議 3.10+）。
2. 在專案目錄執行：

   ```bash
   python app.py
   ```

3. 在視窗中輸入四碼股票代號（例如 `2330`）後按「新增」。

## 技術說明

- 報價來源：TWSE MIS API
- GUI：Tkinter（Python 內建）
- 儲存：`watchlist.json`（JSON 檔）
