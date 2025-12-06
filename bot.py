import os
import re
import asyncio
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from config import Config
from checker import checker

# Validate configuration
if not Config.validate():
    exit(1)

# Initialize Bot Client
bot = Client(
    "telegram_checker_bot",
    api_id=Config.API_ID,      # Bot's own API_ID
    api_hash=Config.API_HASH,  # Bot's own API_HASH
    bot_token=Config.BOT_TOKEN,
    parse_mode=enums.ParseMode.MARKDOWN
)

# User session storage
user_sessions = {}

def extract_numbers(text):
    """Extract phone numbers from text"""
    # Split by multiple delimiters
    delimiters = [',', '\n', ' ', ';', '|', '\t']
    
    for delim in delimiters:
        if delim in text:
            numbers = [num.strip() for num in text.split(delim) if num.strip()]
            if len(numbers) > 1:
                return numbers
    
    # If no delimiter found, return as single item list
    return [text.strip()] if text.strip() else []

def create_contact_button():
    """Create contact developer button"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])

def format_results(results):
    """Format checking results"""
    response = ""
    
    # Registered numbers
    if results["registered"]:
        response += "**✅ ACCOUNT খোলা আছে:**\n"
        for num in results["registered"][:25]:  # Show first 25
            response += f"✅ `{num}`\n"
        if len(results["registered"]) > 25:
            response += f"✅ ... এবং আরও {len(results['registered']) - 25} টি\n"
        response += "\n"
    
    # Not registered numbers
    if results["not_registered"]:
        response += "**🔒 ACCOUNT খোলা নেই:**\n"
        for num in results["not_registered"][:25]:
            response += f"🔒 `{num}`\n"
        if len(results["not_registered"]) > 25:
            response += f"🔒 ... এবং আরও {len(results['not_registered']) - 25} টি\n"
        response += "\n"
    
    # Invalid format numbers
    if results["invalid_format"]:
        response += f"**⚠️ ভুল ফরম্যাট ({len(results['invalid_format'])} টি):**\n"
        response += "এই নাম্বারগুলো ভুল ফরম্যাটে দেওয়া হয়েছে\n\n"
    
    # Errors
    if results["errors"]:
        response += f"**❌ Errors ({len(results['errors'])}):**\n"
        for err in results["errors"][:5]:
            response += f"• `{err['phone']}` - {err['error'][:50]}\n"
        response += "\n"
    
    # Summary
    total_checked = len(results["registered"]) + len(results["not_registered"])
    response += "**📊 সারাংশ:**\n"
    response += f"• মোট চেক করা: {total_checked} টি নাম্বার\n"
    response += f"• ✅ খোলা: {len(results['registered'])} টি\n"
    response += f"• 🔒 বন্ধ: {len(results['not_registered'])} টি\n"
    
    if results["invalid_format"]:
        response += f"• ⚠️ ভুল ফরম্যাট: {len(results['invalid_format'])} টি\n"
    
    return response

# ==================== COMMAND HANDLERS ====================

@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Initialize user session
    user_sessions[user_id] = {
        "step": "waiting_api_id",
        "api_id": None,
        "api_hash": None
    }
    
    welcome_text = (
        "👋 **Telegram Number Checker Bot**\n\n"
        "📌 **এই বট দিয়ে আপনি যেকোনো নাম্বার চেক করতে পারবেন:**\n"
        "• নাম্বারে টেলিগ্রাম অ্যাকাউন্ট আছে কিনা\n"
        "• একসাথে অনেকগুলো নাম্বার চেক করুন\n"
        "• বাংলাদেশী ফরম্যাট সাপোর্ট\n\n"
        "🔑 **প্রথমে আপনার API Credentials দিন:**\n\n"
        "**ধাপ ১:** আপনার **API_ID** দিন\n"
        "(6-7 ডিজিটের সংখ্যা, my.telegram.org থেকে)\n\n"
        "👉 **API_ID** লিখুন:"
    )
    
    await message.reply_text(welcome_text, reply_markup=create_contact_button())

@bot.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    help_text = (
        "🆘 **সাহায্য - Telegram Number Checker Bot**\n\n"
        "**কমান্ডস:**\n"
        "• /start - বট শুরু করুন\n"
        "• /help - সাহায্য দেখুন\n"
        "• /new - নতুন API credentials দিয়ে শুরু করুন\n"
        "• /cancel - বর্তমান প্রক্রিয়া বাতিল করুন\n\n"
        "**API Credentials পাওয়ার উপায়:**\n"
        "1. https://my.telegram.org/auth এ যান\n"
        "2. লগইন করুন (ফোন নাম্বার + কোড)\n"
        "3. **API Development Tools** এ ক্লিক করুন\n"
        "4. App তৈরি করুন\n"
        "5. **App ID (API_ID)** এবং **App Hash (API_HASH)** পাবেন\n\n"
        "**নাম্বার ফরম্যাট:**\n"
        "• `+8801712345678` (আন্তর্জাতিক)\n"
        "• `8801712345678`\n"
        "• `01712345678` (বাংলাদেশ)\n"
        "• কমা, স্পেস বা নতুন লাইনে আলাদা করুন\n\n"
        "**লিমিট:** একবারে সর্বোচ্চ ৫০ নাম্বার\n\n"
        "📞 **সমস্যা হলে Contact করুন:**"
    )
    
    await message.reply_text(help_text, reply_markup=create_contact_button())

@bot.on_message(filters.command("new"))
async def new_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {
        "step": "waiting_api_id",
        "api_id": None,
        "api_hash": None
    }
    
    await message.reply_text(
        "🔄 **নতুন API Credentials দিয়ে শুরু করুন**\n\n"
        "👉 আপনার **API_ID** দিন:"
    )

@bot.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_sessions:
        user_sessions[user_id] = {
            "step": "waiting_api_id",
            "api_id": None,
            "api_hash": None
        }
    
    await message.reply_text(
        "🗑️ **বর্তমান প্রক্রিয়া বাতিল করা হয়েছে।**\n\n"
        "নতুন করে শুরু করতে /start লিখুন।"
    )

# ==================== MESSAGE HANDLER ====================

@bot.on_message(filters.text & filters.private)
async def handle_message(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Ignore commands
    if text.startswith('/'):
        return
    
    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "step": "waiting_api_id",
            "api_id": None,
            "api_hash": None
        }
    
    session = user_sessions[user_id]
    current_step = session["step"]
    
    # Step 1: Waiting for API_ID
    if current_step == "waiting_api_id":
        # Validate API_ID format
        if not re.match(r'^\d{6,7}$', text):
            await message.reply_text(
                "❌ **ভুল API_ID ফরম্যাট!**\n\n"
                "API_ID 6-7 ডিজিটের সংখ্যা হয়।\n"
                "**উদাহরণ:** `1234567`\n\n"
                "👉 **সঠিক API_ID দিন:**"
            )
            return
        
        session["api_id"] = text
        session["step"] = "waiting_api_hash"
        
        await message.reply_text(
            "✅ **API_ID সংরক্ষিত হয়েছে!**\n\n"
            "**ধাপ ২:** এখন আপনার **API_HASH** দিন\n"
            "(32 character এর hex string)\n\n"
            "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`\n\n"
            "👉 **API_HASH লিখুন:**"
        )
    
    # Step 2: Waiting for API_HASH
    elif current_step == "waiting_api_hash":
        # Validate API_HASH format
        if not re.match(r'^[a-f0-9]{32}$', text.lower()):
            await message.reply_text(
                "❌ **ভুল API_HASH ফরম্যাট!**\n\n"
                "API_HASH 32 character এর hex string হয়।\n"
                "সব letters lowercase এ লিখুন।\n\n"
                "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`\n\n"
                "👉 **সঠিক API_HASH দিন:**"
            )
            return
        
        api_id = session["api_id"]
        
        # Validate credentials
        validating_msg = await message.reply_text(
            "🔍 **API Credentials validate করা হচ্ছে...**\n"
            "⏳ কয়েক সেকেন্ড সময় নিতে পারে..."
        )
        
        is_valid = await checker.validate_user_credentials(api_id, text)
        
        if not is_valid:
            await validating_msg.edit_text(
                "❌ **API Credentials ভুল বা অচল!**\n\n"
                "আপনার দেওয়া API_ID এবং API_HASH কাজ করছে না।\n"
                "দয়া করে নিশ্চিত করুন:\n"
                "1. my.telegram.org থেকে সঠিক credentials নিয়েছেন\n"
                "2. credentials সঠিকভাবে কপি করেছেন\n\n"
                "👉 **নতুন API_ID দিয়ে শুরু করুন:**"
            )
            session["step"] = "waiting_api_id"
            session["api_id"] = None
            return
        
        # Save valid credentials
        session["api_hash"] = text
        session["step"] = "ready_for_numbers"
        session["is_valid"] = True
        
        await validating_msg.edit_text(
            "🎉 **CONGRATULATION** 🎉\n\n"
            "✅ **আপনার API Credentials সফলভাবে verify হয়েছে!**\n\n"
            "**এখন আপনার নাম্বার লিস্ট দিন:**\n\n"
            "**ফরম্যাট:**\n"
            "• একক নাম্বার: `+8801712345678`\n"
            "• একাধিক নাম্বার: `+8801712345678, +8801812345678`\n"
            "• স্পেস দিয়ে: `+8801712345678 +8801812345678`\n"
            "• নতুন লাইনে: এক লাইনে একটি নাম্বার\n\n"
            "**লিমিট:** একবারে সর্বোচ্চ ৫০ টি নাম্বার\n\n"
            "👉 **নাম্বার লিস্ট পাঠান:**"
        )
    
    # Step 3: Ready for numbers
    elif current_step == "ready_for_numbers":
        api_id = session.get("api_id")
        api_hash = session.get("api_hash")
        
        if not api_id or not api_hash:
            await message.reply_text(
                "❌ **Credentials পাওয়া যায়নি!**\n"
                "/start লিখে নতুন করে শুরু করুন।"
            )
            return
        
        # Extract numbers
        phone_list = extract_numbers(text)
        
        if not phone_list:
            await message.reply_text(
                "❌ **কোনো নাম্বার পাওয়া যায়নি!**\n\n"
                "দয়া করে নাম্বারগুলো ঠিকভাবে দিন।\n"
                "**উদাহরণ:**\n"
                "`+8801712345678, +8801812345678, 01712345678`"
            )
            return
        
        # Limit check
        if len(phone_list) > 50:
            await message.reply_text(
                f"⚠️ **লিমিট এক্সিড!**\n"
                f"আপনি {len(phone_list)} টি নাম্বার দিয়েছেন।\n"
                f"একবারে সর্বোচ্চ ৫০ টি নাম্বার চেক করা যায়।\n\n"
                f"প্রথম ৫০ টি নাম্বার চেক করা হচ্ছে..."
            )
            phone_list = phone_list[:50]
        
        # Start checking process
        processing_msg = await message.reply_text(
            f"🔍 **নাম্বার চেক শুরু হয়েছে...**\n\n"
            f"📱 **মোট নাম্বার:** {len(phone_list)} টি\n"
            f"⏳ **স্থিতি:** প্রস্তুত হচ্ছে...\n"
            f"⚡ **API ব্যবহার:** {api_id[:3]}...{api_id[-3:]}"
        )
        
        try:
            # Check numbers
            results = await checker.check_numbers(api_id, api_hash, phone_list)
            
            # Format results
            results_text = format_results(results)
            
            # Send final results with contact button
            await processing_msg.edit_text(
                f"✅ **চেকিং সম্পন্ন!**\n\n{results_text}",
                reply_markup=create_contact_button()
            )
            
            # Keep user in ready state for more checks
            session["step"] = "ready_for_numbers"
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if credentials became invalid
            if any(word in error_msg for word in ["api_id", "auth", "invalid", "unauthorized"]):
                await processing_msg.edit_text(
                    "❌ **আপনার API Credentials অচল বা নষ্ট হয়ে গেছে!**\n\n"
                    "সম্ভাব্য কারণ:\n"
                    "• API credentials expire হয়ে গেছে\n"
                    "• Telegram থেকে ban হয়েছে\n"
                    "• Very old credentials\n\n"
                    "👉 **নতুন API credentials দিয়ে শুরু করুন:**\n"
                    "আপনার **API_ID** দিন:"
                )
                session["step"] = "waiting_api_id"
                session["api_id"] = None
                session["api_hash"] = None
            else:
                await processing_msg.edit_text(
                    f"❌ **ত্রুটি হয়েছে!**\n\n"
                    f"**ত্রুটি:** `{str(e)[:100]}`\n\n"
                    f"দয়া করে আবার চেষ্টা করুন বা Developer কে contact করুন।",
                    reply_markup=create_contact_button()
                )
    
    # Unknown state
    else:
        await message.reply_text(
            "🤖 **বটটি শুরু করুন** /start লিখে\n\n"
            "সাহায্যের জন্য /help লিখুন।",
            reply_markup=create_contact_button()
        )

# ==================== BOT STARTUP ====================

print("=" * 60)
print("🤖 TELEGRAM NUMBER CHECKER BOT")
print("=" * 60)
print(f"👤 Bot API ID: {Config.API_ID}")
print(f"🔑 Bot Token: {Config.BOT_TOKEN[:15]}...")
print("=" * 60)
print("\n🚀 Starting bot...")
print("✅ Bot is running! Press Ctrl+C to stop")
print("=" * 60)

if __name__ == "__main__":
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
