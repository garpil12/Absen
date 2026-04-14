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
last_input = {}

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


def get_field(gid, f):
    if f not in ALL_FIELDS:
        return ""
    cur.execute(f"SELECT {f} FROM jobdast WHERE group_id=?", (gid,))
    r = cur.fetchone()
    return safe(r[0]) if r else ""


# ================= FORMAT USER =================
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


def nice_date():
    return datetime.datetime.now().strftime("%d/%m/%Y")


# ================= PANEL (FORMAT SESUAI PERMINTAAN) =================
def build_copy_all(gid):
    h,b,k,t,g,l = get_data(gid)

    return f"""✦ 𝗝𝗢𝗕𝗗𝗘𝗞𝗦 𝗧𝗠𝗢 ✦
 🗓️ {nice_date()}
━━━━━━━━━━━━━━━━

◆ 𝗛𝗢𝗦𝗧 🎙️    :
{format_user(h)}

◆ 𝙃𝙊𝙎𝙏 𝘽𝘼𝘾𝙆𝙐𝙋 🎧     :
{format_user(b)}

◆ 𝗞𝗘𝗟𝗜𝗟𝗜𝗡𝗚 📝  :
{format_user(k)}

◆ 𝙏𝘼𝙂𝘼𝙇𝙇 🧾   :
{format_text(t)}

◆ 𝙂𝘾𝘼𝙎𝙏 📂   :
{format_text(g)}

◆ 𝙇𝙄𝙉𝙆 📌   :
{format_text(l)}

━━━━━━━━━━━━━━━━
🛍️ @storegarf
"""


# ================= PANEL TEXT =================
def panel_text(gid):
    return build_copy_all(gid)


# ================= BUTTON =================
def panel_btn(gid):
    return [
        [Button.inline("HOST 🎙️", b"jobdast:host"), Button.inline("DEL", b"jobdast:reset_host")],
        [Button.inline("BACKUP ⚙️", b"jobdast:backup"), Button.inline("DEL", b"jobdast:reset_backup")],
        [Button.inline("KELILING 🧾", b"jobdast:keliling"), Button.inline("DEL", b"jobdast:reset_keliling")],

        [
            Button.inline("TAGALL 📂", b"jobdast:tagall"),
            Button.inline("VIEW 👁️", b"jobdast:view_tagall"),
            Button.inline("DEL 🧹", b"jobdast:reset_tagall")
        ],
        [
            Button.inline("GCAST📨", b"jobdast:gcast"),
            Button.inline("VIEW 👁️", b"jobdast:view_gcast"),
            Button.inline("DEL 🧹", b"jobdast:reset_gcast")
        ],
        [
            Button.inline("LINK 📌", b"jobdast:link"),
            Button.inline("VIEW 👁️", b"jobdast:view_link"),
            Button.inline("DEL 🧹", b"jobdast:reset_link")
        ],

        [Button.inline("COPY ALL 💻", b"jobdast:copy_all")],
        [Button.inline("RESET ALL 🚨", b"jobdast:reset_all")]
    ]


# ================= REFRESH =================
async def refresh(client, gid):
    if gid in panel_msg:
        try:
            await panel_msg[gid].edit(panel_text(gid), buttons=panel_btn(gid))
        except:
            pass


# ================= REGISTER =================
def register_jobdast_handlers(client):

    @client.on(events.NewMessage(pattern="/getjobdast"))
    async def panel(event):
        gid = event.chat_id
        init_group(gid)

        msg = await event.reply(panel_text(gid), buttons=panel_btn(gid))
        panel_msg[gid] = msg


    @client.on(events.CallbackQuery(pattern=b"^jobdast:"))
    async def cb(ev):

        uid = ev.sender_id
        gid = ev.chat_id
        data = ev.data.decode().replace("jobdast:", "")

        user = await ev.get_sender()
        name = user.first_name or "User"

        try:

            if data in FIELDS_USER:
                old = get_field(gid, data)
                new = add_user(old, uid, name)

                cur.execute(f"UPDATE jobdast SET {data}=? WHERE group_id=?", (new, gid))
                db.commit()

                await ev.answer("ADDED")
                return await refresh(client, gid)

            if data in FIELDS_TEXT:
                user_state[(uid, gid)] = data
                return await ev.answer("REPLY KE BOT", alert=True)

            if data.startswith("view_"):
                field = data.replace("view_", "")
                text = get_field(gid, field)

                await ev.respond(format_text(text))
                return

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
                if f in ALL_FIELDS:
                    cur.execute(f"UPDATE jobdast SET {f}='' WHERE group_id=?", (gid,))
                    db.commit()

                await ev.answer("DELETED")
                return await refresh(client, gid)

            if data == "copy_all":
                await ev.respond(build_copy_all(gid))
                return

        except Exception as e:
            await ev.answer(f"ERROR: {e}", alert=True)


    @client.on(events.NewMessage(incoming=True))
    async def input_text(event):

        if not event.is_group:
            return

        uid = event.sender_id
        gid = event.chat_id

        key = user_state.get((uid, gid))
        if key not in FIELDS_TEXT:
            return

        text = (event.raw_text or "").strip()
        if not text:
            return

        if last_input.get((uid, gid)) == text:
            return
        last_input[(uid, gid)] = text

        old = get_field(gid, key)
        new = add_text(old, text)

        cur.execute(f"UPDATE jobdast SET {key}=? WHERE group_id=?", (new, gid))
        db.commit()

        user_state.pop((uid, gid), None)

        await event.reply(f"{key.upper()} SAVED ✅")
        await refresh(client, gid)
