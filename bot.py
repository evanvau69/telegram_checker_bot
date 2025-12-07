import os
import re
import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from config import Config
from checker import checker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration
is_valid, validation_msg = Config.validate()
if not is_valid:
    logger.error(f"Configuration error: {validation_msg}")
    print("❌ ERROR: Missing or invalid credentials")
    print("Please set these environment variables:")
    print("1. API_ID (from my.telegram.org)")
    print("2. API_HASH (from my.telegram.org)")
    print("3. BOT_TOKEN (from @BotFather)")
    exit(1)

logger.info("✅ Configuration validated successfully")

# User session management
user_sessions = {}

def create_contact_button():
    """Create contact developer button"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])

def extract_phone_numbers(text):
    """Extract phone numbers from text"""
    numbers = []
    lines = text.strip().split('\n')
    
    for line in lines:
        # Split by common delimiters
        parts = re.split(r'[,;|\s]+', line)
        for part in parts:
            if part.strip():
                numbers.append(part.strip())
    
    return numbers

def format_checking_results(results):
    """Format results for display"""
    response = ""
    
    # Registered numbers
    if results["registered"]:
        response += "**✅ ACCOUNT খোলা আছে:**\n"
        for num in results["registered"][:20]:
            response += f"✅ `{num}`\n"
        if len(results["registered"]) > 20:
            response += f"✅ ... এবং আরও {len(results['registered']) - 20} টি\n"
        response += "\n"
    
    # Not registered numbers
    if results["not_registered"]:
        response += "**🔒 ACCOUNT খোলা নেই:**\n"
        for num in results["not_registered"][:20]:
            response += f"🔒 `{num}`\n"
        if len(results["not_registered"]) > 20:
            response += f"🔒 ... এবং আরও {len(results['not_registered']) - 20} টি\n"
        response += "\n"
    
    # Invalid numbers
    if results["invalid"]:
        response += f"**⚠️ ভুল ফরম্যাট ({len(results['invalid'])} টি):**\n"
        for num in results["invalid"][:5]:
            response += f"⚠️ `{num}`\n"
        response += "\n"
    
    # Errors
    if results["errors"]:
        response += f"**❌ Errors ({len(results['errors'])}):**\n"
        for err in results["errors"][:3]:
            response += f"• {err}\n"
        response += "\n"
    
    # Summary
    total_checked = len(results["registered"]) + len(results["not_registered"])
    response += "**📊 সারাংশ:**\n"
    response += f"• মোট চেক করা: {total_checked} টি\n"
    response += f"• ✅ খোলা: {len(results['registered'])} টি\n"
    response += f"• 🔒 বন্ধ: {len(results['not_registered'])} টি\n"
    
    if results["invalid"]:
        response += f"• ⚠️ ভুল ফরম্যাট: {len(results['invalid'])} টি\n"
    
    return response

# Initialize bot client
bot = Client(
    "telegram_number_checker",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    parse_mode=enums.ParseMode.MARKDOWN,
    sleep_threshold=60
)

# ==================== COMMAND HANDLERS ====================

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Initialize user session
    user_sessions[user_id] = {
        "step": "waiting_api_id",
        "api_id": None,
        "api_hash": None
    }
    
    welcome_message = (
        "👋 **টেলিগ্রাম নাম্বার চেকার বট**\n\n"
        "✅ **এই বট দিয়ে আপনি চেক করতে পারবেন:**\n"
        "• ফোন নাম্বারে টেলিগ্রাম অ্যাকাউন্ট আছে কিনা\n"
        "• একসাথে অনেকগুলো নাম্বার\n\n"
        "📝 **ব্যবহার করার নিয়ম:**\n"
        "1. আপনার **API_ID** দিন (my.telegram.org থেকে)\n"
        "2. আপনার **API_HASH** দিন\n"
        "3. নাম্বার লিস্ট দিন চেক করার জন্য\n\n"
        "**এখন প্রথম ধাপ:**\n"
        "👉 আপনার **API_ID** দিন (6-8 ডিজিটের সংখ্যা):"
    )
    
    await message.reply(welcome_message, reply_markup=create_contact_button())
    logger.info(f"User {user_id} started bot")

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = (
        "🆘 **সাহায্য - টেলিগ্রাম নাম্বার চেকার**\n\n"
        "**কমান্ডস:**\n"
        "• /start - বট শুরু করুন\n"
        "• /help - সাহায্য দেখুন\n"
        "• /new - নতুন API ক্রেডেনশিয়াল দিয়ে শুরু করুন\n"
        "• /status - বট স্ট্যাটাস দেখুন\n\n"
        "**API ক্রেডেনশিয়াল পাওয়ার উপায়:**\n"
        "1. https://my.telegram.org এ যান\n"
        "2. লগইন করুন\n"
        "3. **API Development Tools** এ ক্লিক করুন\n"
        "4. App তৈরি করুন\n"
        "5. **App ID** (API_ID) এবং **App Hash** (API_HASH) নিন\n\n"
        "**নাম্বার ফরম্যাট:**\n"
        "• +8801712345678\n"
        "• 8801712345678\n"
        "• 01712345678\n"
        "• কমা, স্পেস বা নতুন লাইনে আলাদা করুন\n\n"
        "**Contact Developer:**"
    )
    
    await message.reply(help_text, reply_markup=create_contact_button())

@bot.on_message(filters.command("new") & filters.private)
async def new_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {
        "step": "waiting_api_id",
        "api_id": None,
        "api_hash": None
    }
    
    await message.reply(
        "🔄 **নতুন API ক্রেডেনশিয়াল দিয়ে শুরু করা হচ্ছে...**\n\n"
        "👉 আপনার **API_ID** দিন:"
    )

@bot.on_message(filters.command("status") & filters.private)
async def status_command(client: Client, message: Message):
    active_users = len(user_sessions)
    await message.reply(
        f"📊 **বট স্ট্যাটাস:**\n\n"
        f"• ✅ **স্ট্যাটাস:** চালু\n"
        f"• 👥 **এক্টিভ ইউজার:** {active_users}\n"
        f"• 🚀 **হোস্ট:** Railway.app\n"
        f"• 📞 **ডেভেলপার:** @Mr_Evan3490\n\n"
        f"সবকিছু ঠিকঠাক চলছে! ✅"
    )

# ==================== MESSAGE HANDLER ====================

@bot.on_message(filters.text & filters.private)
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Ignore commands
    if text.startswith('/'):
        return
    
    # Ensure user session exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "step": "waiting_api_id",
            "api_id": None,
            "api_hash": None
        }
        await message.reply("⚠️ **সেশন এক্সপায়ার্ড!**\n\n/start লিখে নতুন করে শুরু করুন।")
        return
    
    session = user_sessions[user_id]
    current_step = session.get("step", "waiting_api_id")
    
    # STEP 1: Waiting for API_ID
    if current_step == "waiting_api_id":
        # Validate API_ID format
        if not re.match(r'^\d{6,8}$', text):
            await message.reply(
                "❌ **ভুল API_ID ফরম্যাট!**\n\n"
                "API_ID 6-8 ডিজিটের সংখ্যা হয়।\n"
                "**উদাহরণ:** `1234567`\n\n"
                "👉 **সঠিক API_ID দিন:**"
            )
            return
        
        session["api_id"] = text
        session["step"] = "waiting_api_hash"
        
        await message.reply(
            "✅ **API_ID সংরক্ষিত হয়েছে!**\n\n"
            "**ধাপ ২:** এখন আপনার **API_HASH** দিন\n"
            "(32 character এর hex string)\n\n"
            "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`\n\n"
            "👉 **API_HASH লিখুন:**"
        )
    
    # STEP 2: Waiting for API_HASH
    elif current_step == "waiting_api_hash":
        # Validate API_HASH format
        if not re.match(r'^[a-f0-9]{32}$', text.lower()):
            await message.reply(
                "❌ **ভুল API_HASH ফরম্যাট!**\n\n"
                "API_HASH 32 character এর hex string হয়।\n"
                "সব letters lowercase এ লিখুন।\n\n"
                "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`\n\n"
                "👉 **সঠিক API_HASH দিন:**"
            )
            return
        
        api_id = session.get("api_id")
        
        # Show validating message
        validating_msg = await message.reply("🔍 **API ক্রেডেনশিয়াল চেক করা হচ্ছে...**")
        
        # Save API_HASH
        session["api_hash"] = text
        session["step"] = "ready_for_numbers"
        
        await validating_msg.edit_text(
            "🎉 **CONGRATULATION** 🎉\n\n"
            "✅ **আপনার API ক্রেডেনশিয়াল একসেপ্টেড!**\n\n"
            "**এখন আপনার নাম্বার লিস্ট দিন:**\n\n"
            "**ফরম্যাট:**\n"
            "+8801712345678\n"
            "8801812345678\n"
            "01712345678\n\n"
            "বা কমা/স্পেস দিয়ে আলাদা করুন।\n\n"
            "**লিমিট:** একবারে সর্বোচ্চ ৫০ টি নাম্বার"
        )
    
    # STEP 3: Ready for phone numbers
    elif current_step == "ready_for_numbers":
        api_id = session.get("api_id")
        api_hash = session.get("api_hash")
        
        if not api_id or not api_hash:
            await message.reply("❌ **ক্রেডেনশিয়াল পাওয়া যায়নি!** /start লিখে শুরু করুন।")
            session["step"] = "waiting_api_id"
            return
        
        # Extract phone numbers
        phone_numbers = extract_phone_numbers(text)
        
        if not phone_numbers:
            await message.reply("❌ **কোনো নাম্বার পাওয়া যায়নি!** নাম্বারগুলো ঠিকভাবে দিন।")
            return
        
        # Apply limit
        if len(phone_numbers) > Config.MAX_NUMBERS_PER_REQUEST:
            await message.reply(
                f"⚠️ **লিমিট এক্সিড!**\n"
                f"আপনি {len(phone_numbers)} টি নাম্বার দিয়েছেন।\n"
                f"একবারে সর্বোচ্চ {Config.MAX_NUMBERS_PER_REQUEST} টি নাম্বার চেক করা যায়।\n\n"
                f"প্রথম {Config.MAX_NUMBERS_PER_REQUEST} টি নাম্বার চেক করা হচ্ছে..."
            )
            phone_numbers = phone_numbers[:Config.MAX_NUMBERS_PER_REQUEST]
        
        # Start checking process
        processing_msg = await message.reply(
            f"🔍 **নাম্বার চেক শুরু হয়েছে...**\n\n"
            f"📱 **মোট নাম্বার:** {len(phone_numbers)} টি\n"
            f"⏳ **স্থিতি:** প্রস্তুত হচ্ছে...\n"
            f"⚡ **API ব্যবহার:** {api_id[:3]}...{api_id[-3:]}"
        )
        
        try:
            # Check numbers
            results = await checker.check_multiple_numbers(api_id, api_hash, phone_numbers)
            
            # Format results
            results_text = format_checking_results(results)
            
            # Send final results
            await processing_msg.edit_text(
                f"✅ **চেকিং সম্পন্ন!**\n\n{results_text}",
                reply_markup=create_contact_button()
            )
            
            # Keep user in ready state for more checks
            session["step"] = "ready_for_numbers"
            
            logger.info(f"User {user_id} checked {len(phone_numbers)} numbers")
            
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Error for user {user_id}: {error_msg}")
            
            # Check if credentials became invalid
            if any(word in error_msg for word in ["api", "auth", "invalid", "unauthorized"]):
                await processing_msg.edit_text(
                    "❌ **আপনার API ক্রেডেনশিয়াল অচল বা নষ্ট হয়ে গেছে!**\n\n"
                    "সম্ভাব্য কারণ:\n"
                    "• API credentials expire হয়ে গেছে\n"
                    "• Telegram থেকে ban হয়েছে\n"
                    "• ভুল ক্রেডেনশিয়াল\n\n"
                    "👉 **নতুন API ক্রেডেনশিয়াল দিয়ে শুরু করুন:**\n"
                    "আপনার **API_ID** দিন:"
                )
                session["step"] = "waiting_api_id"
                session["api_id"] = None
                session["api_hash"] = None
            else:
                await processing_msg.edit_text(
                    f"❌ **ত্রুটি হয়েছে!**\n\n"
                    f"ত্রুটি: `{str(e)[:100]}`\n\n"
                    f"দয়া করে আবার চেষ্টা করুন বা Developer কে contact করুন।",
                    reply_markup=create_contact_button()
                )

# ==================== STARTUP ====================

async def main():
    """Main function to run the bot"""
    logger.info("🚀 Starting Telegram Number Checker Bot on Railway...")
    
    try:
        await bot.start()
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"✅ Bot started successfully! Username: @{me.username}")
        
        print("\n" + "="*60)
        print(f"🤖 BOT: @{me.username}")
        print(f"📞 DEVELOPER: @Mr_Evan3490")
        print(f"🚀 HOST: Railway.app")
        print(f"✅ STATUS: RUNNING")
        print("="*60)
        print("\n📢 Send /start to your bot to begin!")
        print("="*60)
        
        # Keep bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ ERROR: {e}")
    finally:
        await bot.stop()
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
