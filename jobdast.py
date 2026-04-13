from telethon import events, Button
import sqlite3, datetime

db = sqlite3.connect("tmo.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS jobdast(
    group_id INTEGER PRIMARY KEY,
    host TEXT,
    backup TEXT,
    keliling TEXT,
    tagall TEXT,
    gcast TEXT,
    link TEXT
)
""")
db.commit()

panel_msg = {}
user_state = {}

FIELDS_USER = ["host", "backup", "keliling"]
FIELDS_TEXT = ["tagall", "gcast", "link"]

# ================= INIT =================
def init_group(gid):
    cur.execute("INSERT OR IGNORE INTO jobdast(group_id) VALUES(?)", (gid,))
    db.commit()

def safe(x):
    return x or ""

# ================= DATA =================
def get_data(gid):
    init_group(gid)
    cur.execute("""
        SELECT host,backup,keliling,tagall,gcast,link
        FROM jobdast WHERE group_id=?
    """, (gid,))
    return cur.fetchone() or ("", "", "", "", "", "")

def get_field(gid, f):
    cur.execute(f"SELECT {f} FROM jobdast WHERE group_id=?", (gid,))
    r = cur.fetchone()
    return safe(r[0]) if r else ""

# ================= FORMAT USER =================
def format_user(x):
    if not x:
        return "-"
    out = []
    for v in [i for i in x.split("\n") if i.strip()]:
        try:
            uid, name = v.split("|", 1)
            out.append(f"• [{name}](tg://user?id={uid})")
        except:
            out.append(f"• {v}")
    return "\n".join(out)

# ================= FORMAT TEXT =================
def format_text(x):
    if not x:
        return "-"
    return "\n".join([i for i in x.split("\n") if i.strip()])

# ================= ADD =================
def add_user(old, uid, name):
    entry = f"{uid}|{name}"
    return entry if not old else old + "\n" + entry

def add_text(old, text):
    text = text.strip()
    return text if not old else old + "\n" + text

# ================= DATE =================
def nice_date():
    return datetime.datetime.now().strftime("%A, %d %B %Y")

# ================= PANEL =================
def build_copy_all(gid):
    h,b,k,t,g,l = get_data(gid)

    return f"""┏━━━━━━━━━━━━━━━━━━━━━━┓
        ✨ 𝗝𝗢𝗕𝗗𝗘𝗞𝗦 𝗧𝗠𝗢 ✨
┗━━━━━━━━━━━━━━━━━━━━━━┛

🎙️ 𝗛𝗢𝗦𝗧
{format_user(h)}

🛡 𝗛𝗢𝗦𝗧 𝗕𝗔𝗖𝗞𝗨𝗣
{format_user(b)}

📍 𝗞𝗘𝗟𝗜𝗡𝗚
{format_user(k)}

📅 {nice_date()}
━━━━━━━━━━━━━━━━━━━━━━

📣 𝗧𝗔𝗚𝗔𝗟𝗟
{format_text(t)}

📡 𝗚𝗖𝗔𝗦𝗧
{format_text(g)}

🔗 𝗟𝗜𝗡𝗞
{format_text(l)}

━━━━━━━━━━━━━━━━━━━━━━

⚡ 𝗣𝗢𝗪𝗘𝗥 𝗕𝗬 @Brisik23
🛍 𝗠𝘆 𝘀𝘁𝗼𝗿𝗲: @storegraf
"""

def panel_text(gid):
    return build_copy_all(gid)

# ================= BUTTON =================
def panel_btn(gid):
    return [
        [Button.inline("🎙️ 𝗛𝗢𝗦𝗧", b"host"), Button.inline("🧨 DEL", b"reset_host")],
        [Button.inline("🛡 𝙃𝙊𝙎𝙏 𝘽𝘼𝘾𝙆𝙐𝙋", b"backup"), Button.inline("🧨 DEL", b"reset_backup")],
        [Button.inline("📍 𝗞𝗘𝗟𝗜𝗡𝗚", b"keliling"), Button.inline("🧨 DEL", b"reset_keliling")],

        [Button.inline("📣 𝙏𝘼𝙂𝘼𝙇𝙇", b"tagall"), Button.inline("👁 PREVIEW", b"preview_tagall"), Button.inline("🧨 DEL", b"reset_tagall")],
        [Button.inline("📡 𝙂𝘾𝘼𝙎𝙏", b"gcast"), Button.inline("👁 PREVIEW", b"preview_gcast"), Button.inline("🧨 DEL", b"reset_gcast")],
        [Button.inline("🔗 𝙇𝙄𝙉𝙆", b"link"), Button.inline("👁 PREVIEW", b"preview_link"), Button.inline("🧨 DEL", b"reset_link")],

        [Button.inline("📋 𝘾𝙊𝙋𝙋𝙔  𝘼𝙇𝙇", b"copy_all")],
        [Button.inline("🧨 𝙍𝙀𝙎𝙀𝙏 𝘼𝙇𝙇", b"reset_all")]
    ]

# ================= REFRESH =================
async def refresh(client, gid):
    if gid in panel_msg:
        await panel_msg[gid].edit(panel_text(gid), buttons=panel_btn(gid))

# ================= HANDLER =================
def register_jobdast_handlers(client):

    @client.on(events.NewMessage(pattern="/getjobdast"))
    async def panel(event):
        gid = event.chat_id
        init_group(gid)

        msg = await event.reply(panel_text(gid), buttons=panel_btn(gid))
        panel_msg[gid] = msg

    @client.on(events.NewMessage(pattern="/help"))
    async def help_cmd(event):
        await event.reply("""
━━━━━━━━━━━━━━
🔥 JOBDESK HELP

• Klik tombol field
• Reply ke bot untuk save
• Preview = teks bersih
• DEL = hapus data
• COPY ALL = ambil semua
━━━━━━━━━━━━━━
""")

    # ================= CALLBACK =================
    @client.on(events.CallbackQuery)
    async def cb(ev):
        uid = ev.sender_id
        gid = ev.chat_id
        data = ev.data.decode()

        user = await ev.get_sender()
        name = user.first_name or "User"

        if data in FIELDS_USER:
            old = get_field(gid, data)
            new = add_user(old, uid, name)

            cur.execute(f"UPDATE jobdast SET {data}=? WHERE group_id=?", (new, gid))
            db.commit()

            await ev.answer("ADDED USER ✅")
            return await refresh(client, gid)

        if data in FIELDS_TEXT:
            user_state[(uid, gid)] = data
            return await ev.answer("REPLY KE BOT SEKARANG", alert=True)

        if data.startswith("preview_"):
            field = data.replace("preview_", "")
            text = get_field(gid, field)
            await ev.respond(format_text(text))

        if data == "reset_all":
            cur.execute("""
                UPDATE jobdast SET host='',backup='',keliling='',
                tagall='',gcast='',link=''
                WHERE group_id=?
            """, (gid,))
            db.commit()
            await ev.answer("RESET DONE")
            return await refresh(client, gid)

        if data.startswith("reset_"):
            f = data.replace("reset_", "")
            cur.execute(f"UPDATE jobdast SET {f}='' WHERE group_id=?", (gid,))
            db.commit()
            await ev.answer(f"{f.upper()} DELETED")
            return await refresh(client, gid)

        if data == "copy_all":
            await ev.respond(build_copy_all(gid))

    # ================= FIX INPUT TEXT =================
    @client.on(events.NewMessage)
    async def input_text(event):
        uid = event.sender_id
        gid = event.chat_id

        key = user_state.get((uid, gid))
        if not key:
            return

        text = event.raw_text
        old = get_field(gid, key)
        new = add_text(old, text)

        cur.execute(f"UPDATE jobdast SET {key}=? WHERE group_id=?", (new, gid))
        db.commit()

        user_state.pop((uid, gid))

        await event.reply(f"{key.upper()} SAVED ✅")
        await refresh(client, gid)

print("BOT AKTIF 🔥")
