from telethon import events, Button
import sqlite3, datetime

# ==============================
#  INIT DB
# ==============================
db = sqlite3.connect("tmo.db")
cur = db.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS jobdast(
    id INTEGER PRIMARY KEY,
    host TEXT,
    backup TEXT,
    keliling TEXT,
    tagall TEXT,
    gcast TEXT
)
""")
cur.execute("INSERT OR IGNORE INTO jobdast(id) VALUES(1)")
db.commit()


# ==============================
#  TEMPLATE ESTETIK
# ==============================
def template_jobdast():
    cur.execute("SELECT host,backup,keliling FROM jobdast WHERE id=1")
    h, b, k = cur.fetchone()

    # list keliling
    k_list = ""
    if k:
        for idx, x in enumerate(k.split(","), 1):
            k_list += f"{idx}. {x}\n"
    else:
        k_list = "1.\n2.\n3.\n"

    tgl = datetime.datetime.now().strftime("%d %B %Y")

    return f"""
<b>𝗝𝗢𝗕𝗗𝗘𝗦𝗞 𝗧𝗠𝗢 — {tgl}</b>

𝗛𝗢𝗦𝗧 :
1. {h or ''}

𝗕𝗔𝗖𝗞𝗨𝗣 :
1. {b or ''}

𝗞𝗘𝗟𝗜𝗡𝗚 :
{k_list}

𝗞𝗜𝗥𝗜𝗠 𝗞𝗔𝗧𝗔² 𝗧𝗔𝗚 𝗔𝗟𝗟 / 𝗕𝗨𝗞𝗔𝗜𝗡 𝗠𝗜𝗖 : <b>ALL ADMIN</b>
"""


# ==============================
#  REGISTER HANDLERS KE CLIENT
# ==============================
def register_jobdast_handlers(client):

    # /getjobdast
    @client.on(events.NewMessage(pattern="/getjobdast"))
    async def get_job(event):
        msg = template_jobdast()
        await event.reply(
            msg,
            buttons=[
                [Button.inline("✏ Edit Host", b"edithost")],
                [Button.inline("✏ Edit Backup", b"editbackup")],
                [Button.inline("✏ Edit Keliling", b"editkeliling")],
                [Button.inline("🗑 Hapus Jobdast", b"deljob")],
            ],
            parse_mode="html"
        )

    # CALLBACK EDIT
    @client.on(events.CallbackQuery(data=b"edithost"))
    async def cb_host(ev):
        await ev.edit("Kirim: <code>/savejobdast host NAMA</code>", parse_mode="html")

    @client.on(events.CallbackQuery(data=b"editbackup"))
    async def cb_backup(ev):
        await ev.edit("Kirim: <code>/savejobdast backup NAMA</code>", parse_mode="html")

    @client.on(events.CallbackQuery(data=b"editkeliling"))
    async def cb_kel(ev):
        await ev.edit("Kirim: <code>/savejobdast keliling nama1,nama2,nama3</code>", parse_mode="html")

    # SAVE JOBDAST
    @client.on(events.NewMessage(pattern=r"/savejobdast (.+) (.+)"))
    async def save_jobdast(event):
        tipe = event.pattern_match.group(1).lower()
        isi = event.pattern_match.group(2)

        if tipe == "host":
            cur.execute("UPDATE jobdast SET host=? WHERE id=1", (isi,))
        elif tipe == "backup":
            cur.execute("UPDATE jobdast SET backup=? WHERE id=1", (isi,))
        elif tipe == "keliling":
            cur.execute("UPDATE jobdast SET keliling=? WHERE id=1", (isi,))
        else:
            return await event.reply("Tipe tidak valid.")

        db.commit()
        await event.reply("✅ Tersimpan!\nKetik /getjobdast untuk lihat hasil.")

    # DELETE JOBDAST
    @client.on(events.NewMessage(pattern="/deljobdast"))
    async def del_job(event):
        cur.execute("UPDATE jobdast SET host=NULL, backup=NULL, keliling=NULL")
        db.commit()
        await event.reply("🗑 Semua jobdast dihapus!")

    # SAVE tagall & gcast
    @client.on(events.NewMessage(pattern=r"/save (tagall|gcast) (.+)"))
    async def save_text(event):
        tipe = event.pattern_match.group(1)
        text = event.pattern_match.group(2)

        cur.execute(f"UPDATE jobdast SET {tipe}=? WHERE id=1", (text,))
        db.commit()

        await event.reply(f"✅ Kata-kata <b>{tipe}</b> tersimpan!", parse_mode="html")

    # /gettmo
    @client.on(events.NewMessage(pattern="/gettmo"))
    async def get_tmo(event):
        cur.execute("SELECT tagall, gcast FROM jobdast WHERE id=1")
        tagall, gcast = cur.fetchone()

        await event.reply(
            "<b>KATA-KATA TMO</b>\n\nKlik tombol untuk menyalin otomatis.",
            buttons=[
                [Button.copy(text="📣 TagAll", data=tagall or "Belum disimpan")],
                [Button.copy(text="📤 Gcast", data=gcast or "Belum disimpan")]
            ],
            parse_mode="html"
        )

    print(">> Modul JOBDAST TMO aktif.")
