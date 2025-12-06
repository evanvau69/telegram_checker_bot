import os
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from checker import checker

# Load environment
load_dotenv()

# Bot configuration - ONLY NEED BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN not found in .env file!")
    print("Please create a .env file with BOT_TOKEN=your_token_here")
    exit(1)

# Initialize bot
app = Client(
    "telegram_number_checker",
    bot_token=BOT_TOKEN
)

# User states storage (in-memory, simple)
user_states = {}

def extract_numbers(text):
    """Extract phone numbers from text"""
    numbers = []
    
    # Split by common delimiters
    for delim in [',', '\n', ' ', ';', '|']:
        if delim in text:
            parts = [p.strip() for p in text.split(delim) if p.strip()]
            numbers.extend(parts)
            break
    else:
        numbers.append(text.strip())
    
    return numbers

def format_results(results):
    """Format results with emojis"""
    response = ""
    
    if results["registered"]:
        response += "**✅ Account খোলা আছে:**\n"
        for num in results["registered"][:30]:  # Limit display
            response += f"✅ `{num}`\n"
        if len(results["registered"]) > 30:
            response += f"✅ ... এবং আরও {len(results['registered']) - 30} টি\n"
        response += "\n"
    
    if results["not_registered"]:
        response += "**🔒 Account খোলা নেই:**\n"
        for num in results["not_registered"][:30]:
            response += f"🔒 `{num}`\n"
        if len(results["not_registered"]) > 30:
            response += f"🔒 ... এবং আরও {len(results['not_registered']) - 30} টি\n"
        response += "\n"
    
    # Summary
    total_checked = len(results["registered"]) + len(results["not_registered"])
    response += f"**📊 সারাংশ:**\n"
    response += f"• মোট চেকড: {total_checked} টি\n"
    response += f"• ✅ খোলা: {len(results['registered'])} টি\n"
    response += f"• 🔒 বন্ধ: {len(results['not_registered'])} টি\n"
    
    if results["invalid"]:
        response += f"• ⚠️ ভুল ফরম্যাট: {len(results['invalid'])} টি\n"
    
    return response

# Start command
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Reset user state
    user_states[user_id] = {"step": "idle"}
    
    welcome_text = (
        "👋 **Telegram Number Checker Bot**\n\n"
        "এই বট দিয়ে আপনি যেকোনো টেলিগ্রাম নাম্বার চেক করতে পারবেন।\n\n"
        "**কিভাবে ব্যবহার করবেন:**\n"
        "1. আপনার **API_ID** দিন (my.telegram.org থেকে)\n"
        "2. আপনার **API_HASH** দিন\n"
        "3. নাম্বার লিস্ট দিন চেক করার জন্য\n\n"
        "**এখন প্রথম ধাপ:**\n"
        "আপনার **API_ID** দিন (6-7 ডিজিটের সংখ্যা):"
    )
    
    # Set state to wait for API_ID
    user_states[user_id] = {"step": "waiting_api_id"}
    
    contact_button = InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])
    
    await message.reply_text(welcome_text, reply_markup=contact_button)

# Handle all messages
@app.on_message(filters.text & filters.private)
async def message_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Skip commands
    if text.startswith('/'):
        return
    
    # Initialize user state if not exists
    if user_id not in user_states:
        user_states[user_id] = {"step": "idle"}
    
    current_state = user_states[user_id].get("step", "idle")
    
    # Step 1: Waiting for API_ID
    if current_state == "waiting_api_id":
        # Validate API_ID format
        if not re.match(r'^\d{6,7}$', text):
            await message.reply_text(
                "❌ **ভুল API_ID!**\n"
                "API_ID 6-7 ডিজিটের সংখ্যা হয়।\n"
                "**উদাহরণ:** `1234567`\n\n"
                "আবার API_ID দিন:"
            )
            return
        
        # Save API_ID
        user_states[user_id]["api_id"] = text
        user_states[user_id]["step"] = "waiting_api_hash"
        
        await message.reply_text(
            "✅ **API_ID সংরক্ষিত!**\n\n"
            "**দ্বিতীয় ধাপ:**\n"
            "এখন আপনার **API_HASH** দিন (32 character hex):\n\n"
            "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`"
        )
    
    # Step 2: Waiting for API_HASH
    elif current_state == "waiting_api_hash":
        # Validate API_HASH format
        if not re.match(r'^[a-f0-9]{32}$', text.lower()):
            await message.reply_text(
                "❌ **ভুল API_HASH!**\n"
                "API_HASH 32 character এর hex string হয়।\n"
                "**উদাহরণ:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`\n\n"
                "আবার API_HASH দিন:"
            )
            return
        
        # Get API_ID from state
        api_id = user_states[user_id].get("api_id")
        if not api_id:
            await message.reply_text("❌ **ত্রুটি!** /start লিখে আবার শুরু করুন।")
            user_states[user_id] = {"step": "idle"}
            return
        
        # Validate credentials
        validating_msg = await message.reply_text("🔍 **API Credentials চেক করা হচ্ছে...**")
        
        is_valid = await checker.validate_api_credentials(api_id, text)
        
        if not is_valid:
            await validating_msg.edit_text(
                "❌ **API Credentials ভুল বা কাজ করছে না!**\n\n"
                "আপনি যে API_ID এবং Hash দিয়েছেন তা সঠিক নয়।\n"
                "দয়া করে নতুন করে শুরু করুন:\n\n"
                "আপনার **API_ID** দিন:"
            )
            user_states[user_id] = {"step": "waiting_api_id"}
            return
        
        # Save valid credentials
        user_states[user_id]["api_hash"] = text
        user_states[user_id]["step"] = "ready_for_numbers"
        user_states[user_id]["credentials_valid"] = True
        
        await validating_msg.edit_text(
            "🎉 **CONGRATULATION** 🎉\n\n"
            "✅ **আপনার API Credentials সফলভাবে verify হয়েছে!**\n\n"
            "**এখন আপনার নাম্বার লিস্ট দিন:**\n\n"
            "**ফরম্যাট:**\n"
            "• `+8801712345678`\n"
            "• `+8801712345678, +8801812345678`\n"
            "• `+8801712345678 +8801812345678`\n"
            "• নতুন লাইনে আলাদা করেও দিতে পারেন\n\n"
            "**লিমিট:** একবারে সর্বোচ্চ 100 টি নাম্বার"
        )
    
    # Step 3: Ready for numbers
    elif current_state == "ready_for_numbers":
        # Get credentials from state
        api_id = user_states[user_id].get("api_id")
        api_hash = user_states[user_id].get("api_hash")
        
        if not api_id or not api_hash:
            await message.reply_text("❌ **Credentials পাওয়া যায়নি!** /start লিখে আবার শুরু করুন।")
            user_states[user_id] = {"step": "idle"}
            return
        
        # Extract numbers
        phone_list = extract_numbers(text)
        
        if not phone_list:
            await message.reply_text(
                "❌ **কোনো নাম্বার পাওয়া যায়নি!**\n\n"
                "দয়া করে ফোন নাম্বারগুলো ঠিকভাবে দিন।\n"
                "**উদাহরণ:** `+8801712345678, +8801812345678`"
            )
            return
        
        # Limit check
        if len(phone_list) > 100:
            await message.reply_text(
                f"⚠️ **লিমিট এক্সিড!**\n"
                f"আপনি {len(phone_list)} টি নাম্বার দিয়েছেন।\n"
                f"একবারে সর্বোচ্চ 100 টি নাম্বার চেক করা যায়।\n\n"
                f"প্রথম 100 টি নাম্বার চেক করা হচ্ছে..."
            )
            phone_list = phone_list[:100]
        
        # Start checking
        processing_msg = await message.reply_text(
            f"🔍 **নাম্বার চেক করা হচ্ছে...**\n"
            f"মোট নাম্বার: {len(phone_list)} টি\n\n"
            f"⏳ প্রস্তুত হচ্ছে...\n\n"
            f"**স্থিতি:** API ব্যবহার করা হচ্ছে"
        )
        
        try:
            # Check numbers
            results = await checker.check_bulk(api_id, api_hash, phone_list)
            
            # Format results
            results_text = format_results(results)
            
            # Add contact button
            contact_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
            ]])
            
            # Send final results
            await processing_msg.edit_text(
                f"✅ **চেকিং সম্পন্ন!**\n\n{results_text}",
                reply_markup=contact_button
            )
            
            # Keep user ready for more checks
            user_states[user_id]["step"] = "ready_for_numbers"
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if credentials are invalid
            if "api_id" in error_msg or "auth" in error_msg or "invalid" in error_msg:
                await processing_msg.edit_text(
                    "❌ **আপনার API Credentials অচল বা নষ্ট হয়ে গেছে!**\n\n"
                    "দয়া করে নতুন API credentials দিয়ে শুরু করুন:\n\n"
                    "আপনার **API_ID** দিন:"
                )
                user_states[user_id] = {"step": "waiting_api_id"}
            else:
                await processing_msg.edit_text(
                    f"❌ **ত্রুটি হয়েছে!**\n\n"
                    f"ত্রুটি: `{str(e)[:150]}`\n\n"
                    f"দয়া করে আবার চেষ্টা করুন।"
                )
    
    # Unknown state
    else:
        await message.reply_text(
            "🤖 **বটটি শুরু করুন** /start লিখে\n\n"
            "বা সাহায্যের জন্য /help লিখুন।"
        )

# Help command
@app.on_message(filters.command("help"))
async def help_handler(client: Client, message: Message):
    help_text = (
        "🆘 **Telegram Number Checker Bot - Help**\n\n"
        "**কমান্ডস:**\n"
        "• /start - শুরু করুন\n"
        "• /help - এই সাহায্য মেনু\n"
        "• /new - নতুন API credentials দিয়ে শুরু করুন\n\n"
        "**কিভাবে API credentials পাবেন:**\n"
        "1. https://my.telegram.org/apps এ যান\n"
        "2. লগইন করুন\n"
        "3. **API Development Tools** এ ক্লিক করুন\n"
        "4. **App title** এবং **Short name** দিন\n"
        "5. **App ID** (API_ID) এবং **App Hash** (API_HASH) পাবেন\n\n"
        "**নাম্বার ফরম্যাট:**\n"
        "• `+8801712345678` (পূর্ণ ফরম্যাট)\n"
        "• `8801712345678`\n"
        "• `01712345678` (বাংলাদেশের জন্য)\n\n"
        "**সমস্যা হলে Contact করুন:**"
    )
    
    contact_button = InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])
    
    await message.reply_text(help_text, reply_markup=contact_button)

# New command - restart with new credentials
@app.on_message(filters.command("new"))
async def new_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "waiting_api_id"}
    
    await message.reply_text(
        "🔄 **নতুন API credentials দিয়ে শুরু করুন**\n\n"
        "আপনার **API_ID** দিন (6-7 ডিজিটের সংখ্যা):"
    )

# Cleanup on stop
@app.on_raw_update()
async def cleanup():
    checker.cleanup()

# Run bot
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Telegram Number Checker Bot")
    print("=" * 50)
    print("\n⚙️  Bot Configuration:")
    print(f"• Token: {'Set' if BOT_TOKEN else 'NOT SET!'}")
    print("\n🚀 Starting bot...")
    print("Press Ctrl+C to stop\n")
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        checker.cleanup()
        print("🧹 Cleanup completed")
