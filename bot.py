import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from config import Config
from checker import checker

# Check credentials
valid, message = Config.check()
if not valid:
    print(f"❌ ERROR: {message}")
    print("Please create a .env file with:")
    print("API_ID=your_api_id_from_my.telegram.org")
    print("API_HASH=your_api_hash_from_my.telegram.org")
    print("BOT_TOKEN=your_token_from_BotFather")
    exit(1)

print("✅ Credentials loaded successfully!")
print(f"🤖 Bot starting with API_ID: {Config.API_ID}")

# Bot initialization with CORRECT Pyrogram 2.0+ syntax
bot = Client(
    "telegram_checker_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

# User states (simple in-memory)
user_data = {}

def get_contact_button():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])

def extract_numbers(text):
    """Extract phone numbers from text"""
    # Remove extra spaces and split
    numbers = []
    for line in text.split('\n'):
        for part in line.split(','):
            for item in part.split(' '):
                if item.strip():
                    numbers.append(item.strip())
    return numbers

def format_results(results):
    """Format results for display"""
    text = ""
    
    if results["registered"]:
        text += "**✅ ACCOUNT খোলা আছে:**\n"
        for num in results["registered"][:20]:
            text += f"✅ `{num}`\n"
        if len(results["registered"]) > 20:
            text += f"✅ ... এবং আরও {len(results['registered']) - 20} টি\n"
        text += "\n"
    
    if results["not_registered"]:
        text += "**🔒 ACCOUNT খোলা নেই:**\n"
        for num in results["not_registered"][:20]:
            text += f"🔒 `{num}`\n"
        if len(results["not_registered"]) > 20:
            text += f"🔒 ... এবং আরও {len(results['not_registered']) - 20} টি\n"
        text += "\n"
    
    if results["invalid"]:
        text += f"**⚠️ ভুল ফরম্যাট ({len(results['invalid'])} টি):**\n"
        for num in results["invalid"][:5]:
            text += f"⚠️ `{num}`\n"
        text += "\n"
    
    # Summary
    checked = len(results["registered"]) + len(results["not_registered"])
    text += f"**📊 সারাংশ:**\n"
    text += f"• মোট চেকড: {checked} টি\n"
    text += f"• ✅ খোলা: {len(results['registered'])} টি\n"
    text += f"• 🔒 বন্ধ: {len(results['not_registered'])} টি\n"
    
    return text

@bot.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "wait_api_id"}
    
    text = (
        "👋 **Telegram Number Checker Bot**\n\n"
        "🔍 **এই বট দিয়ে চেক করুন:**\n"
        "• নাম্বারে Telegram Account আছে কিনা\n"
        "• একসাথে অনেকগুলো নাম্বার\n\n"
        "📝 **কিভাবে ব্যবহার করবেন:**\n"
        "1. আপনার **API_ID** দিন (my.telegram.org থেকে)\n"
        "2. আপনার **API_HASH** দিন\n"
        "3. Verify হলে নাম্বার লিস্ট দিন\n\n"
        "**এখন প্রথম ধাপ:**\n"
        "👉 আপনার **API_ID** দিন:"
    )
    
    await message.reply(text, reply_markup=get_contact_button())

@bot.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    text = (
        "🆘 **সাহায্য - Telegram Number Checker**\n\n"
        "**কমান্ডস:**\n"
        "• /start - শুরু করুন\n"
        "• /help - সাহায্য\n"
        "• /new - নতুন API দিয়ে শুরু করুন\n\n"
        "**API Credentials পাবার উপায়:**\n"
        "1. https://my.telegram.org এ যান\n"
        "2. লগইন করুন\n"
        "3. **API Development Tools** এ ক্লিক করুন\n"
        "4. App তৈরি করুন\n"
        "5. **App ID** (API_ID) এবং **App Hash** (API_HASH) নিন\n\n"
        "**নাম্বার ফরম্যাট:**\n"
        "• +8801712345678\n"
        "• 8801712345678\n"
        "• 01712345678\n"
        "• কমা বা স্পেস দিয়ে আলাদা করুন\n\n"
        "**Contact Developer:**"
    )
    
    await message.reply(text, reply_markup=get_contact_button())

@bot.on_message(filters.command("new"))
async def new_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "wait_api_id"}
    await message.reply("🔄 **নতুন API credentials দিয়ে শুরু করুন**\n\n👉 আপনার **API_ID** দিন:")

@bot.on_message(filters.text & filters.private)
async def message_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text.startswith('/'):
        return
    
    if user_id not in user_data:
        user_data[user_id] = {"step": "wait_api_id"}
    
    step = user_data[user_id].get("step", "wait_api_id")
    
    # Step 1: Wait for API_ID
    if step == "wait_api_id":
        if not re.match(r'^\d{6,8}$', text):
            await message.reply("❌ **ভুল API_ID!** 6-8 ডিজিটের সংখ্যা দিন:\n\n👉 আবার **API_ID** দিন:")
            return
        
        user_data[user_id]["api_id"] = text
        user_data[user_id]["step"] = "wait_api_hash"
        await message.reply("✅ **API_ID সেভ হয়েছে!**\n\n👉 এখন আপনার **API_HASH** দিন (32 character hex):")
    
    # Step 2: Wait for API_HASH
    elif step == "wait_api_hash":
        if not re.match(r'^[a-f0-9]{32}$', text.lower()):
            await message.reply("❌ **ভুল API_HASH!** 32 character hex string দিন:\n\n👉 আবার **API_HASH** দিন:")
            return
        
        api_id = user_data[user_id].get("api_id")
        
        # Validate credentials
        msg = await message.reply("🔍 **API Credentials validate করা হচ্ছে...**")
        
        is_valid = await checker.validate_user_api(api_id, text)
        
        if not is_valid:
            await msg.edit("❌ **API Credentials ভুল!**\n\n👉 নতুন **API_ID** দিয়ে শুরু করুন:")
            user_data[user_id] = {"step": "wait_api_id"}
            return
        
        user_data[user_id]["api_hash"] = text
        user_data[user_id]["step"] = "wait_numbers"
        user_data[user_id]["valid"] = True
        
        await msg.edit(
            "🎉 **CONGRATULATION** 🎉\n\n"
            "✅ **আপনার API Credentials verify হয়েছে!**\n\n"
            "**এখন নাম্বার লিস্ট দিন:**\n\n"
            "**ফরম্যাট:**\n"
            "+8801712345678\n"
            "8801812345678\n"
            "01712345678\n\n"
            "বা কমা/স্পেস দিয়ে আলাদা করুন।"
        )
    
    # Step 3: Wait for numbers
    elif step == "wait_numbers":
        api_id = user_data[user_id].get("api_id")
        api_hash = user_data[user_id].get("api_hash")
        
        if not api_id or not api_hash:
            await message.reply("❌ **Credentials নেই!** /start লিখে শুরু করুন।")
            return
        
        numbers = extract_numbers(text)
        
        if not numbers:
            await message.reply("❌ **কোনো নাম্বার নেই!** নাম্বার দিন:")
            return
        
        if len(numbers) > 50:
            numbers = numbers[:50]
            await message.reply(f"⚠️ **50 টির বেশি নাম্বার!** প্রথম 50 টি চেক করা হবে।")
        
        processing = await message.reply(f"🔍 **চেকিং শুরু...**\n\n📱 **মোট:** {len(numbers)} টি\n⏳ **প্রসেসিং...**")
        
        try:
            results = await checker.check_bulk(api_id, api_hash, numbers)
            
            results_text = format_results(results)
            
            await processing.edit(
                f"✅ **চেকিং সম্পন্ন!**\n\n{results_text}",
                reply_markup=get_contact_button()
            )
            
            user_data[user_id]["step"] = "wait_numbers"
            
        except Exception as e:
            error = str(e).lower()
            if "api" in error or "auth" in error:
                await processing.edit(
                    "❌ **API Credentials নষ্ট হয়েছে!**\n\n"
                    "👉 নতুন **API_ID** দিয়ে শুরু করুন:",
                    reply_markup=get_contact_button()
                )
                user_data[user_id] = {"step": "wait_api_id"}
            else:
                await processing.edit(
                    f"❌ **Error:** `{error[:100]}`\n\n"
                    "দয়া করে আবার চেষ্টা করুন।",
                    reply_markup=get_contact_button()
                )

# Run bot with CORRECT Pyrogram 2.0+ pattern
async def main():
    async with bot:
        print("🤖 Bot is running...")
        await bot.run()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Telegram Number Checker Bot")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
