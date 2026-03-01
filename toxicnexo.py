from telethon import TelegramClient, events, Button
import asyncio
import os

# ============ CONFIGURATION ============
# আপনার দেওয়া তথ্য অনুযায়ী আপডেট করা হয়েছে
API_ID = 37663020 
API_HASH = 'e082fa08c56c6f30e2855fbec3d2969b'
BOT_TOKEN = '8569155953:AAGWVZ1m3h4ezGZUCEFmt-w0m5-7SEJtQow' 
ADMIN_ID = 7408644813 

# সেশন সেভ করার জন্য ফোল্ডার
SESSIONS_DIR = 'sessions'
os.makedirs(SESSIONS_DIR, exist_ok=True)

class ToxicNexoBot:
    def __init__(self):
        self.bot = TelegramClient('bot_session', API_ID, API_HASH)
        self.pending_phone = {}
        self.pending_otp = {}
        self.temp_clients = {}

    async def run(self):
        # বট স্টার্ট
        await self.bot.start(bot_token=BOT_TOKEN)
        print("✅ Toxicnexo Bot is Online!")
        
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            welcome_text = (
                "🤖 **Welcome to Toxicnexo AI**\n\n"
                "You can manage your accounts and monitor OTPs from here.\n\n"
                "©️ @PBC_COMMUNITY"
            )
            buttons = [[Button.inline("📱 Add Account", b"add_account")]]
            await event.reply(welcome_text, buttons=buttons)

        @self.bot.on(events.CallbackQuery(data=b"add_account"))
        async def add_account_start(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("⚠️ Access Denied!", alert=True)
                return
            self.pending_phone[event.sender_id] = True
            await event.edit("📱 Enter phone number with country code (e.g., +88017...):")

        @self.bot.on(events.NewMessage)
        async def handle_text(event):
            user_id = event.sender_id
            
            # ফোন নম্বর হ্যান্ডেল করা
            if user_id in self.pending_phone:
                del self.pending_phone[user_id]
                phone = event.text.strip()
                client = TelegramClient(f'{SESSIONS_DIR}/{phone}', API_ID, API_HASH)
                await client.connect()
                try:
                    result = await client.send_code_request(phone)
                    self.temp_clients[user_id] = {'client': client, 'phone': phone, 'hash': result.phone_code_hash}
                    self.pending_otp[user_id] = True
                    await event.reply("🔢 Enter the **OTP** sent to your Telegram app:")
                except Exception as e:
                    await event.reply(f"❌ Error: {e}")
            
            # OTP হ্যান্ডেল করা
            elif user_id in self.pending_otp:
                otp_code = event.text.strip()
                data = self.temp_clients[user_id]
                try:
                    await data['client'].sign_in(data['phone'], otp_code, phone_code_hash=data['hash'])
                    await event.reply(f"✅ Account Added Successfully: {data['phone']}")
                    
                    # অ্যাডমিনকে জানানো
                    await self.bot.send_message(ADMIN_ID, f"🚀 **New Account Linked**\nPhone: `{data['phone']}`")
                    del self.pending_otp[user_id]
                except Exception as e:
                    await event.reply(f"❌ Invalid OTP or Error: {e}")

        await self.bot.run_until_disconnected()

if __name__ == '__main__':
    bot = ToxicNexoBot()
    asyncio.run(bot.run())
      
