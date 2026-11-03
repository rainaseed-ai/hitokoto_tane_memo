import datetime
import json
import os
import tkinter as tk
from tkinter import font as tkfont

import requests
import sys

# ==================== 設定 ====================
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEMO_FILE = os.path.join(BASE_DIR, "memos.json")

# ローカルLLMの設定（Ollama想定。未導入なら None のままでOK）
LLM_ENABLED = True                 # False にするとLLM機能をオフにできる
LLM_API_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "llama3"               # 使っているモデル名に変更（例: aya, gemma2, mistral）
# ==============================================

WINDOW_W, WINDOW_H = 360, 420


def load_memos():
    """保存済みメモを読み込む"""
    if not os.path.exists(MEMO_FILE):
        return []
    try:
        with open(MEMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_memos(memos):
    """メモをJSONで保存"""
    with open(MEMO_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=2)


def ask_local_llm(text):
    """ローカルLLMにお返事をもらう。失敗したら None を返す"""
    if not LLM_ENABLED:
        return None
    try:
        resp = requests.post(
            LLM_API_URL,
            json={
                "model": LLM_MODEL,
                "prompt": (
                    "次のメモに対して、簡潔で優しくコメントしてください。\n"
                    f"メモ: {text}\n"
                    "回答:"
                ),
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip() or None
    except Exception:
        # LLMが動いていない場合は静かに諦める（初心者向けの挙動）
        return None


class MemoPad(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("メモ帳")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.attributes("-topmost", True)   # 常に前面
        self.minsize(WINDOW_W, 200)

        self.memos = load_memos()

        # ---- UI ----
        header_font = tkfont.Font(size=9)
        title_font = tkfont.Font(size=11, weight="bold")

        tk.Label(self, text="ひとこと種🌱", font=title_font).pack(pady=(8, 2))

        self.date_label = tk.Label(self, fg="gray", font=header_font)
        self.date_label.pack(pady=(0, 4))

        self.text = tk.Text(self, wrap="word", relief="flat", bg="#fff5f7")
        self.text.pack(fill="both", expand=True, padx=10, pady=4)
        self.text.focus_set()

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=6)

        tk.Button(btn_frame, text="💾 保存", command=self.save_memo).pack(side="left", padx=4)
        tk.Button(btn_frame, text="📜 履歴", command=self.toggle_history).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✖ 閉じる", command=self.destroy).pack(side="left", padx=4)

        self.status = tk.Label(self, text="", fg="gray", font=header_font)
        self.status.pack(pady=(0, 6))

        self.history_visible = False
        self.history_text = None

        self.update_date()
        self.bind("<Control-s>", lambda e: self.save_memo())

    # ---------------- 機能 ----------------
    def update_date(self):
        today = datetime.date.today().strftime("%Y-%m-%d (%a)")
        self.date_label.config(text=f"📅 {today}")
        self.after(60_000, self.update_date)   # 1分ごとに更新

    def save_memo(self):
        content = self.text.get("1.0", "end").strip()
        if not content:
            self.status.config(text="何も書かれていないよ？")
            return

        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.status.config(text="保存中…")

        reply = ask_local_llm(content)
        entry = {
            "datetime": stamp,
            "memo": content,
            "llm_reply": reply,   # None の場合は履歴で「(LLMなし)」と表示
        }
        self.memos.append(entry)
        save_memos(self.memos)

        if reply:
            self.status.config(text=f"保存したよ！LLMのお返事も一緒に✨")
        else:
            self.status.config(text="保存したよ！（LLMは休憩中）")

        self.text.delete("1.0", "end")
        if self.history_visible:
            self.refresh_history()
    def toggle_history(self):
        if self.history_visible:
            # 履歴を閉じて、入力欄を戻す
            self.history_text.destroy()
            self.history_text = None
            self.history_visible = False
            self.text.pack(fill="both", expand=True, padx=10, pady=4)
            return

        # 入力欄を隠して、履歴をその場所に表示
        self.text.pack_forget()
        self.history_visible = True
        self.history_text = tk.Text(self, wrap="word", relief="flat", bg="#f5f5ff")
        self.history_text.pack(fill="both", expand=True, padx=10, pady=4)
        self.refresh_history()
    

    def refresh_history(self):
        if not self.history_text:
            return
        self.history_text.delete("1.0", "end")
        if not self.memos:
            self.history_text.insert("end", "まだ何もないよ。最初のメモを書いてみて！")
            return
        for entry in reversed(self.memos):
            self.history_text.insert("end", f'■ {entry["datetime"]}\n')
            self.history_text.insert("end", f'{entry["memo"]}\n')
            reply = entry.get("llm_reply")
            if reply:
                self.history_text.insert("end", f'🤖 {reply}\n')
            else:
                self.history_text.insert("end", "🤖 (LLMなし)\n")
            self.history_text.insert("end", "\n")


if __name__ == "__main__":
    app = MemoPad()
    app.mainloop()