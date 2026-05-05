import json
import threading
import time
import urllib.parse
import urllib.request
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

API_BASE = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?json=1&delay=0&ex_ch="
STORE_PATH = Path(__file__).with_name("watchlist.json")
REFRESH_SECONDS = 5


def load_watchlist() -> list[str]:
    if not STORE_PATH.exists():
        return []
    try:
        data = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(x) for x in data if str(x).isdigit() and len(str(x)) == 4]
    except Exception:
        pass
    return []


def save_watchlist(codes: list[str]) -> None:
    STORE_PATH.write_text(json.dumps(codes, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_stock(code: str) -> dict:
    # 嘗試上市(tse)與上櫃(otc)來源，修正四碼代號無資料的問題。
    channels = [f"tse_{code}.tw", f"otc_{code}.tw"]
    query = "|".join(channels)
    url = API_BASE + urllib.parse.quote(query, safe="|_")

    with urllib.request.urlopen(url, timeout=8) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    payload = json.loads(raw)
    msg_array = payload.get("msgArray") or []

    info = None
    for row in msg_array:
        if row.get("n") and row.get("z") != "-":
            info = row
            break
    if info is None and msg_array:
        info = msg_array[0]
    if not info:
        raise ValueError("查無資料")

    name = info.get("n") or "未知名稱"
    now_raw = info.get("z")
    bid_raw = info.get("b", "").split("_")[0]
    prev_raw = info.get("y")

    def to_float(v: str | None) -> float:
        try:
            if v in (None, "", "-"):
                return float("nan")
            return float(v)
        except ValueError:
            return float("nan")

    now = to_float(now_raw)
    if now != now:  # NaN
        now = to_float(bid_raw)
    prev = to_float(prev_raw)
    diff = now - prev if now == now and prev == prev else float("nan")

    return {"code": code, "name": name, "price": now, "diff": diff}


class StockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("台股偷看盤（桌面版）")
        self.root.geometry("760x520")

        self.codes = load_watchlist()
        self.rows: dict[str, str] = {}

        self.build_ui()
        self.refresh()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(frame)
        header.pack(fill=tk.X)

        ttk.Label(header, text="台股偷看盤（自訂視窗）", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="尚未更新")
        ttk.Label(header, textvariable=self.time_var).pack(side=tk.RIGHT)

        control = ttk.Frame(frame)
        control.pack(fill=tk.X, pady=(12, 8))

        ttk.Label(control, text="股票代號：").pack(side=tk.LEFT)
        self.code_var = tk.StringVar()
        code_entry = ttk.Entry(control, textvariable=self.code_var, width=10)
        code_entry.pack(side=tk.LEFT)
        code_entry.bind("<Return>", lambda _e: self.add_code())

        ttk.Button(control, text="新增", command=self.add_code).pack(side=tk.LEFT, padx=6)
        ttk.Button(control, text="移除選取", command=self.remove_selected).pack(side=tk.LEFT)
        ttk.Button(control, text="立即更新", command=self.refresh).pack(side=tk.RIGHT)

        self.tree = ttk.Treeview(frame, columns=("code", "name", "price", "diff"), show="headings", height=16)
        for col, text, width, anchor in [
            ("code", "代號", 100, tk.CENTER),
            ("name", "名稱", 260, tk.W),
            ("price", "現價", 120, tk.E),
            ("diff", "漲跌", 120, tk.E),
        ]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(fill=tk.BOTH, expand=True)

    def add_code(self):
        code = self.code_var.get().strip()
        if not code.isdigit() or len(code) != 4:
            messagebox.showerror("格式錯誤", "請輸入四碼數字股票代號，例如 2330")
            return
        if code in self.codes:
            messagebox.showinfo("已存在", f"{code} 已在清單中")
            return
        self.codes.append(code)
        save_watchlist(self.codes)
        self.code_var.set("")
        self.refresh()

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for item_id in selected:
            code = self.tree.item(item_id, "values")[0]
            if code in self.codes:
                self.codes.remove(code)
        save_watchlist(self.codes)
        self.refresh()

    def refresh(self):
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        results = []
        for code in self.codes:
            try:
                results.append(fetch_stock(code))
            except Exception:
                results.append({"code": code, "name": "讀取失敗", "price": float("nan"), "diff": float("nan")})
        self.root.after(0, lambda: self._render(results))

    def _render(self, results: list[dict]):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in results:
            price = "--" if row["price"] != row["price"] else f"{row['price']:.2f}"
            diff = "--" if row["diff"] != row["diff"] else f"{row['diff']:+.2f}"
            self.tree.insert("", tk.END, values=(row["code"], row["name"], price, diff))

        self.time_var.set(f"更新時間：{time.strftime('%H:%M:%S')}")
        self.root.after(REFRESH_SECONDS * 1000, self.refresh)


if __name__ == "__main__":
    app_root = tk.Tk()
    StockApp(app_root)
    app_root.mainloop()
