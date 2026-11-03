from datetime import datetime
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

DB_NAME = "memo_app.db"


class MemoApp:

    def __init__(self, root):
        self.root = root
        self.root.title("ひとこと種🌱")
        self.root.geometry("380x340")
        self.root.attributes("-topmost", True)  # 最前面に表示固定（小窓化）

        # データベース初期化と画面構築
        self.init_db()
        self.create_widgets()

        # 時計（日付表示）の自動更新を開始
        self.update_clock()

    # --------------------------------------------------
    # 1. データベースの初期化
    # --------------------------------------------------
    def init_db(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                content TEXT NOT NULL,
                ai_comment TEXT
            )
        """)
        conn.commit()
        conn.close()

    # --------------------------------------------------
    # 2. 今日の日付・時刻を自動表示（1分ごとに更新）
    # --------------------------------------------------
    def update_clock(self):
        now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        self.date_label.config(text=f"📅 {now_str}")
        self.root.after(60000, self.update_clock)

    # --------------------------------------------------
    # 3. 将来のローカルLLM連携用（ダミー返信）
    # --------------------------------------------------
    def get_llm_reply(self, user_memo: str) -> str:
        return "今日もお疲れ様！ひとこと記録できてえらい！"

    # --------------------------------------------------
    # 4. メモの保存処理
    # --------------------------------------------------
    def save_memo(self):
        content = self.text_input.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("注意", "メモを入力してください。")
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ai_comment = self.get_llm_reply(content)

        # SQLiteに保存
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO memos (created_at, content, ai_comment)
            VALUES (?, ?, ?)
        """,
            (now_str, content, ai_comment),
        )
        conn.commit()
        conn.close()

        # 入力欄をクリアしてステータス更新
        self.text_input.delete("1.0", tk.END)
        self.status_label.config(
            text=f"保存しました ({now_str})\nAI: {ai_comment}"
        )

    # --------------------------------------------------
    # 5. 過去のメモを見返す（履歴サブウィンドウの表示）
    # --------------------------------------------------
    def show_history(self):
        # 新しいサブウィンドウ（Pop-up）を作成
        history_win = tk.Toplevel(self.root)
        history_win.title("過去のメモ一覧")
        history_win.geometry("550x300")
        history_win.attributes("-topmost", True)

        # 一覧表示（Treeview）の作成
        columns = ("created_at", "content", "ai_comment")
        tree = ttk.Treeview(history_win, columns=columns, show="headings")

        tree.heading("created_at", text="日時")
        tree.heading("content", text="メモ内容")
        tree.heading("ai_comment", text="AIの返信")

        tree.column("created_at", width=140, anchor="center")
        tree.column("content", width=220, anchor="w")
        tree.column("ai_comment", width=160, anchor="w")

        # スクロールバーの追加
        scrollbar = ttk.Scrollbar(
            history_win, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        # データベースから新しい順（ID降順）で取得して挿入
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT created_at, content, ai_comment FROM memos ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            created_at, content, ai_comment = row
            tree.insert(
                "",
                "end",
                values=(
                    created_at,
                    content,
                    ai_comment if ai_comment else "（なし）",
                ),
            )

    # --------------------------------------------------
    # 6. GUI画面の構築（パーツの配置）
    # --------------------------------------------------
    def create_widgets(self):
        # 日付自動表示ラベル
        self.date_label = ttk.Label(
            self.root, text="", font=("Helvetica", 9, "bold")
        )
        self.date_label.pack(anchor="w", padx=10, pady=(10, 0))

        # テキスト入力エリア
        label = ttk.Label(self.root, text="今日のひとこと:")
        label.pack(anchor="w", padx=10, pady=(5, 0))

        self.text_input = tk.Text(self.root, height=5, width=40)
        self.text_input.pack(padx=10, pady=5)

        # ボタンエリア（保存＋履歴表示）
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)

        self.save_btn = ttk.Button(
            btn_frame, text="保存する", command=self.save_memo
        )
        self.save_btn.pack(side="left", padx=5)

        self.history_btn = ttk.Button(
            btn_frame, text="📜 履歴を見る", command=self.show_history
        )
        self.history_btn.pack(side="left", padx=5)

        # ステータス／AI返信表示エリア
        self.status_label = ttk.Label(
            self.root, text="メモを入力して保存を押してください", wraplength=350
        )
        self.status_label.pack(padx=10, pady=10)


# --------------------------------------------------
# アプリの起動処理
# --------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = MemoApp(root)
    root.mainloop()
    