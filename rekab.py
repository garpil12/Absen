import sqlite3
import re
from datetime import datetime
from telethon import events, Button

# ======================
# DB
# ======================
db = sqlite3.connect("absen.db", check_same_thread=False)
cur = db.cursor()

# ======================
# TABLE REKAB
# ======================
cur.execute("""
CREATE TABLE IF NOT EXISTS rekab_tmo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    nama TEXT,
    gc TEXT,
    status TEXT DEFAULT 'MISSING',
    note TEXT DEFAULT ''
)
""")
db.commit()

# ======================
# STATE MULTIGROUP
# ======================
page_state = {}

# ======================
# GET DATA
# ======================
def get_data(gid):
    cur.execute("""
        SELECT id, nama, gc, status, note
        FROM rekab_tmo
        WHERE group_id=?
        ORDER BY id ASC
    """, (gid,))
    return cur.fetchall()

# ======================
# STATUS ICON
# ======================
def status_icon(status):
    s = status.upper()
    if s == "MISSING":
        return "🟡 MISSING"
    elif s == "DONE":
        return "🟢 DONE"
    elif s == "CLOSED":
        return "🔴 CLOSED"
    return "⚪ UNKNOWN"

# ======================
# BUILD UI
# ======================
def build(gid, page=1):
    data = get_data(gid)

    total_page = max(1, (len(data) + 4) // 5)
    start = (page - 1) * 5
    rows = data[start:start + 5]

    now = datetime.now()

    text = (
        f"╔═══ 𝗞𝗘𝗟𝗜𝗟𝗜𝗡𝗚 𝗧𝗠𝗢 ═══╗\n"
        f"📅 {now.strftime('%d-%m-%Y')} | PAGE {page}/{total_page}\n"
        f"════════════════════\n\n"
    )

    buttons = []

    for rid, nama, gc, status, note in rows:
        text += (
            f"🔸 ID     : {rid}\n"
            f"🔹 NAME   : {nama}\n"
            f"🔹 LINK   : {gc}\n"
            f"🔹 STATUS : {status_icon(status)}\n"
            f"════════════════════\n\n"
        )

        buttons.append([
            Button.inline("🟡 MISSING", f"miss_{rid}"),
            Button.inline("🟢 DONE", f"done_{rid}"),
            Button.inline("🔴 CLOSED", f"close_{rid}"),
            Button.inline("🗑 DELETE", f"del_{rid}")
        ])

    buttons.append([
        Button.inline("⬅️ Prev", f"prev_{page}"),
        Button.inline("➡️ Next", f"next_{page}")
    ])

    buttons.append([
        Button.inline("📦 PREVIEW ALL", "preview_all")
    ])

    return text, buttons, total_page

# ======================
# REGISTER
# ======================
def register_rekab(client):

    # ======================
    # ADD REKAB (APPEND ONLY + DEBUG)
    # ======================
    @client.on(events.NewMessage(pattern="/addrekab"))
    async def addrekab(event):
        gid = event.chat_id
        raw = event.raw_text.replace("/addrekab", "").strip()

        print(f"[DEBUG] /addrekab masuk group {gid}")
        print(f"[DEBUG] RAW:\n{raw}")

        if not raw:
            await event.respond("❌ kosong")
            return

        count = 0

        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.search(r"(https?://t\.me/\S+|@\w+)", line)
            if not match:
                print(f"[SKIP] no link: {line}")
                continue

            gc = match.group(1)
            nama = line.replace(gc, "").strip() or "UNKNOWN"

            print(f"[INSERT] {nama} | {gc}")

            cur.execute(
                "INSERT INTO rekab_tmo (group_id, nama, gc) VALUES (?,?,?)",
                (gid, nama, gc)
            )
            count += 1

        db.commit()

        print(f"[DEBUG] TOTAL INSERT: {count}")

        await event.respond(f"✅ REKAB MASUK: {count}")

    # ======================
    # SHOW
    # ======================
    @client.on(events.NewMessage(pattern="/rekab"))
    async def rekab(event):
        gid = event.chat_id
        text, buttons, _ = build(gid, 1)

        msg = await event.respond(text, buttons=buttons)
        page_state[gid] = {"page": 1, "msg_id": msg.id}

    # ======================
    # CALLBACK
    # ======================
    @client.on(events.CallbackQuery())
    async def cb(event):

        data = event.data.decode()
        gid = event.chat_id

        try:

            if data.startswith("miss_"):
                rid = int(data.split("_")[1])
                cur.execute("UPDATE rekab_tmo SET status='MISSING' WHERE id=?", (rid,))

            elif data.startswith("done_"):
                rid = int(data.split("_")[1])
                cur.execute("UPDATE rekab_tmo SET status='DONE' WHERE id=?", (rid,))

            elif data.startswith("close_"):
                rid = int(data.split("_")[1])
                cur.execute("UPDATE rekab_tmo SET status='CLOSED' WHERE id=?", (rid,))

            elif data.startswith("del_"):
                rid = int(data.split("_")[1])
                cur.execute("DELETE FROM rekab_tmo WHERE id=?", (rid,))

            elif data == "preview_all":

                rows = get_data(gid)

                text = (
                    f"╔═══ FULL REKAP ═══╗\n"
                    f"📅 {datetime.now().strftime('%d-%m-%Y')}\n"
                    f"📊 TOTAL: {len(rows)}\n"
                    f"════════════════════\n\n"
                )

                for i, (rid, nama, gc, status, note) in enumerate(rows, 1):
                    text += (
                        f"{i}. {nama}\n"
                        f"GC: {gc}\n"
                        f"STATUS: {status_icon(status)}\n"
                        f"════════════════════\n\n"
                    )

                for chunk in [text[i:i+3500] for i in range(0, len(text), 3500)]:
                    await client.send_message(gid, chunk)

                return

            elif data.startswith("prev_") or data.startswith("next_"):

                page = page_state.get(gid, {}).get("page", 1)

                if data.startswith("prev_"):
                    page = max(1, page - 1)
                else:
                    page += 1

                page_state[gid]["page"] = page

                text, buttons, _ = build(gid, page)
                await event.edit(text, buttons=buttons)
                return

            db.commit()

            page = page_state.get(gid, {}).get("page", 1)
            text, buttons, _ = build(gid, page)

            await event.edit(text, buttons=buttons)
            await event.answer("UPDATED ✔️")

        except Exception as e:
            print("[ERROR CALLBACK]", e)
            await event.answer(f"ERROR: {e}", alert=True)
