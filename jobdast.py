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
ALL_FIELDS = FIELDS_USER + FIELDS_TEXT

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

# ================= SAFE FIELD =================
def get_field(gid, f):
    if f not in ALL_FIELDS:
        return ""
    try:
        cur.execute(f"SELECT {f} FROM jobdast WHERE group_id=?", (gid,))
        r = cur.fetchone()
        return safe(r[0]) if r else ""
    except:
        return ""

# ================= FORMAT =================
def format_user(x):
    if not x:
        return "-"
    out = []
    for v in x.split("\n"):
        if not v.strip():
            continue
        try:
            uid, name = v.split("|", 1)
            out.append(f"• [{name}](tg://user?id={uid})")
        except:
            out.append(f"• {v}")
    return "\n".join(out)

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
"""

def panel_text(gid):
    return build_copy_all(gid)

# ================= BUTTON =================
def panel_btn(gid):
    return [
        [Button.inline("HOST", b"host"), Button.inline("DEL", b"reset_host")],
        [Button.inline("BACKUP", b"backup"), Button.inline("DEL", b"reset_backup")],
        [Button.inline("KELILING", b"keliling"), Button.inline("DEL", b"reset_keliling")],

        [Button.inline("TAGALL", b"tagall"), Button.inline("PREVIEW", b"preview_tagall"), Button.inline("DEL", b"reset_tagall")],
        [Button.inline("GCAST", b"gcast"), Button.inline("PREVIEW", b"preview_gcast"), Button.inline("DEL", b"reset_gcast")],
        [Button.inline("LINK", b"link"), Button.inline("PREVIEW", b"preview_link"), Button.inline("DEL", b"reset_link")],

        [Button.inline("COPY ALL", b"copy_all")],
        [Button.inline("🧨 CLEAR FIELD ALL", b"clear_all")],
        [Button.inline("RESET ALL", b"reset_all")]
    ]

# ================= REFRESH =================
async def refresh(client, gid):
    try:
        if gid in panel_msg:
            await panel_msg[gid].edit(panel_text(gid), buttons=panel_btn(gid))
    except:
        pass

# ================= HANDLER =================
def register_jobdast_handlers(client):

    @client.on(events.NewMessage(pattern="/getjobdast"))
    async def panel(event):
        gid = event.chat_id
        init_group(gid)

        msg = await event.reply(panel_text(gid), buttons=panel_btn(gid))
        panel_msg[gid] = msg

    # ================= CALLBACK =================
    @client.on(events.CallbackQuery)
    async def cb(ev):
        uid = ev.sender_id
        gid = ev.chat_id
        data = (ev.data or b"").decode().strip()

        user = await ev.get_sender()
        name = user.first_name or "User"

        if data in FIELDS_USER:
            old = get_field(gid, data)
            new = add_user(old, uid, name)

            cur.execute(f"UPDATE jobdast SET {data}=? WHERE group_id=?", (new, gid))
            db.commit()

            await ev.answer("ADDED USER")
            return await refresh(client, gid)

        if data in FIELDS_TEXT:
            user_state[(uid, gid)] = data
            return await ev.answer("REPLY KE BOT")

        if data.startswith("preview_"):
            field = data.replace("preview_", "")
            await ev.respond(format_text(get_field(gid, field)))
            return

        # RESET ALL
        if data == "reset_all":
            cur.execute("""
                UPDATE jobdast SET host='',backup='',keliling='',
                tagall='',gcast='',link=''
                WHERE group_id=?
            """, (gid,))
            db.commit()
            await ev.answer("RESET DONE")
            return await refresh(client, gid)

        # CLEAR ALL (FIXED + SAFE)
        if data == "clear_all":
            cur.execute("""
                UPDATE jobdast SET host='',backup='',keliling='',
                tagall='',gcast='',link=''
                WHERE group_id=?
            """, (gid,))
            db.commit()
            await ev.answer("CLEARED ALL")
            return await refresh(client, gid)

        if data.startswith("reset_"):
            f = data.replace("reset_", "")
            if f in ALL_FIELDS:
                cur.execute(f"UPDATE jobdast SET {f}='' WHERE group_id=?", (gid,))
                db.commit()

            await ev.answer("DELETED")
            return await refresh(client, gid)

        if data == "copy_all":
            await ev.respond(build_copy_all(gid))

