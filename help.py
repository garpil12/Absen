from telethon import events, Button

def register_help(client):

    @client.on(events.NewMessage(pattern="/help"))
    async def help_handler(event):

        text = """╔══════════════════════╗
      BOT AUTO ABSEN
╚══════════════════════╝

[ SYSTEM READY ]

> FONT
  convert text style
  /font

> AUTO ABSEN
  running auto system

> JOBDESK TMO
  manage group
  /getjobdast

[ STATUS: ONLINE ⚡ ]
"""

        buttons = [
            [Button.url("🛍 MY STORE", "https://t.me/storegraf")],
            [Button.url("⚡ POWER BY", "https://t.me/Brisik23")]
        ]

        await event.reply(text, buttons=buttons)
