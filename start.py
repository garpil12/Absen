from telethon import events, Button
import sqlite3
from datetime import datetime

# ================= CONFIG =================
OWNER_ID = 8209644174

# ================= DB =================
db = sqlite3.connect("users.db", check_same_thread=False)
cur = db.cursor()

# tabel user (tanpa ref)
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    join_date TEXT
)
""")

db.commit()


def register_start(client):

    # ================= UI =================
    def main_menu():
        text = """╭━━━━━━━━━━━━━━━━━━━━━━╮
   ⚡ 𝗕𝗢𝗧 𝗔𝗨𝗧𝗢 𝗔𝗕𝗦𝗘𝗡 ⚡
╰━━━━━━━━━━━━━━━━━━━━━━╯

👋 Haii bro,
gue bot auto absen yang siap bantu
lu handle grup tanpa ribet.

━━━━━━━━━━━━━━━━━━━━━━
⚙️ 𝗙𝗘𝗔𝗧𝗨𝗥𝗘:
• 📋 Jobdesk TMO
• 🔤 Fonts Style
• ⏱ Auto Absen

🔥 Semua jadi otomatis, tinggal pake.
"""
        buttons = [
            [Button.url("🛍 MY STORE", "https://t.me/storegarf")],
            [Button.url("⚡ POWER BY", "https://t.me/Brsik23")]
        ]
        return text, buttons

    # ================= /start =================
    @client.on(events.NewMessage(pattern=r"^/start"))
    async def start(event):
        user_id = event.sender_id

        # ===== simpan user =====
        cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        cek = cur.fetchone()

        if not cek:
            now = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                "INSERT INTO users (user_id, join_date) VALUES (?, ?)",
                (user_id, now)
            )
            db.commit()

        text, buttons = main_menu()

        # auto edit biar gak spam
        try:
            await event.edit(text, buttons=buttons)
        except:
            await event.respond(text, buttons=buttons)

    # ================= /cek (OWNER) =================
    @client.on(events.NewMessage(pattern=r"^/cek"))
    async def cek(event):
        if event.sender_id != OWNER_ID:
            return

        cur.execute("SELECT user_id FROM users")
        data = cur.fetchall()

        text = "📊 DATA USER:\n\n"
        for (u,) in data:
            text += f"{u}\n"

        await event.reply(text)
