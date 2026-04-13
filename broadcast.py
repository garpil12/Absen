from telethon import events
import asyncio
import sqlite3
from telethon.errors import FloodWaitError, RPCError

OWNER_ID = 8209644174

db = sqlite3.connect("broadcast.db", check_same_thread=False)
cur = db.cursor()

# ================= DB =================
cur.execute("""
CREATE TABLE IF NOT EXISTS targets(
id INTEGER PRIMARY KEY,
type TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS blacklist(
id INTEGER PRIMARY KEY
)
""")
db.commit()

# ================= DEBUG =================
def log(msg):
    print(f"[DEBUG] {msg}")

# ================= HELPER =================
def save_target(tid, ttype):
    try:
        cur.execute("INSERT OR IGNORE INTO targets(id,type) VALUES(?,?)", (tid, ttype))
        db.commit()
    except:
        pass

def remove_target(tid):
    cur.execute("DELETE FROM targets WHERE id=?", (tid,))
    db.commit()

def get_targets():
    cur.execute("SELECT id FROM targets WHERE type='group'")
    return [i[0] for i in cur.fetchall()]

def add_bl(gid):
    cur.execute("INSERT OR IGNORE INTO blacklist(id) VALUES(?)", (gid,))
    db.commit()

def del_bl(gid):
    cur.execute("DELETE FROM blacklist WHERE id=?", (gid,))
    db.commit()

def get_bl():
    cur.execute("SELECT id FROM blacklist")
    return [i[0] for i in cur.fetchall()]

# ================= QUEUE =================
broadcast_queue = asyncio.Queue()
broadcast_running = False
WORKERS = 5

# ================= SAFE SEND =================
async def send_safe(client, gid, msg):
    try:
        if msg.media:
            await client.send_file(gid, msg.media, caption=msg.text or "")
        else:
            await client.send_message(gid, msg.text or "")
        return True

    except FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return await send_safe(client, gid, msg)

    except RPCError:
        remove_target(gid)
        add_bl(gid)
        return False

    except:
        return False

# ================= WORKER =================
async def worker(client):
    global broadcast_running
    broadcast_running = True

    while True:
        job = await broadcast_queue.get()
        if job is None:
            break

        msg, status = job

        targets = get_targets()
        blacklist = set(get_bl())

        ok, fail = 0, 0

        for gid in targets:
            if gid in blacklist:
                continue

            if await send_safe(client, gid, msg):
                ok += 1
            else:
                fail += 1

            await asyncio.sleep(0.4)

        try:
            await status.edit(f"✅ DONE\n✔ {ok}\n❌ {fail}\n📊 {len(targets)}")
        except:
            pass

        broadcast_queue.task_done()

    broadcast_running = False

# ================= START WORKERS (FIX UTAMA) =================
def start_workers(client):
    for _ in range(WORKERS):
        client.loop.create_task(worker(client))   # 🔥 FIX ERROR LOOP DI SINI

# ================= RESOLVE =================
async def resolve_id(client, text):
    try:
        if text.startswith("https://t.me/"):
            ent = await client.get_entity(text)
            return ent.id
        return int(text)
    except:
        return None

# ================= REGISTER =================
def register_broadcast(client):

    # ============ CHAT ACTION (JOIN / LEFT BOT) ============
    @client.on(events.ChatAction)
    async def chat_action(event):
        me = await client.get_me()

        # bot masuk / jadi admin
        if (event.user_added or event.user_joined) and event.user_id == me.id:
            save_target(event.chat_id, "group")
            log(f"JOIN {event.chat_id}")

        # bot di kick / keluar
        if (event.user_kicked or event.user_left) and event.user_id == me.id:
            remove_target(event.chat_id)
            log(f"LEFT {event.chat_id}")

    # ============ AUTO SAVE ============
    @client.on(events.NewMessage(incoming=True))
    async def auto_save(event):
        if event.sender_id == OWNER_ID:
            return

        if event.is_group or event.is_channel:
            save_target(event.chat_id, "group")

    # ============ LIST GROUP ============
    @client.on(events.NewMessage(pattern=r"^/listgrup$"))
    async def list_group(event):
        if event.sender_id != OWNER_ID:
            return

        data = get_targets()
        text = "📊 LIST GROUP\n\n"

        for gid in data:
            text += f"• {gid}\n"

        await event.reply(text)

    # ============ BLACKLIST ============
    @client.on(events.NewMessage(pattern=r"^/bl (.+)"))
    async def bl(event):
        if event.sender_id != OWNER_ID:
            return

        gid = await resolve_id(client, event.pattern_match.group(1))
        if gid:
            add_bl(gid)
            await event.reply("🚫 BL OK")

    @client.on(events.NewMessage(pattern=r"^/unbl (.+)"))
    async def unbl(event):
        if event.sender_id != OWNER_ID:
            return

        gid = await resolve_id(client, event.pattern_match.group(1))
        if gid:
            del_bl(gid)
            await event.reply("✅ UNBL OK")

    # ============ GBAN ============
    @client.on(events.NewMessage(pattern=r"^/gban (.+)"))
    async def gban(event):
        if event.sender_id != OWNER_ID:
            return

        gid = await resolve_id(client, event.pattern_match.group(1))
        if gid:
            try:
                await client.delete_dialog(gid)
            except:
                pass

            add_bl(gid)
            remove_target(gid)
            await event.reply("💀 GBAN OK")

    # ============ BROADCAST ============
    @client.on(events.NewMessage(pattern=r"^/broadcast$"))
    async def bc(event):
        if event.sender_id != OWNER_ID:
            return

        if not event.is_reply:
            return await event.reply("reply pesan")

        msg = await event.get_reply_message()
        status = await event.reply("🚀 queued...")

        await broadcast_queue.put((msg, status))

        global broadcast_running
        if not broadcast_running:
            start_workers(client)
