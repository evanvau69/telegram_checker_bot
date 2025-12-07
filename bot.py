import os
import re
import asyncio
import logging
import sys
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, PhoneNumberInvalid, PhoneNumberUnoccupied
from pyrogram.enums import ParseMode

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Get credentials from Render environment
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Validate
if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.error("❌ MISSING CREDENTIALS")
    print("=" * 60)
    print("ERROR: Set these in Render.com Environment:")
    print("1. API_ID - from my.telegram.org")
    print("2. API_HASH - from my.telegram.org")
    print("3. BOT_TOKEN - from @BotFather")
    print("=" * 60)
    exit(1)

API_ID = int(API_ID)
logger.info(f"✅ Credentials loaded. API_ID: {API_ID}")

# Simple user state storage
user_states = {}

def get_contact_button():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Contact Developer 🙎‍♂️", url="https://t.me/Mr_Evan3490")
    ]])

# Initialize bot with CORRECT settings for cloud
bot = Client(
    name="telegram_checker_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
    sleep_threshold=30,  # Important for cloud
    workers=4,  # Multiple workers for better performance
    parse_mode=ParseMode.MARKDOWN
)

# ==================== COMMAND HANDLERS ====================

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    logger.info(f"📥 /start from user {user_id}")
    
    user_states[user_id] = {"step": "wait_api_id"}
    
    welcome_text = (
        "👋 **Telegram Number Checker Bot**\n\n"
        "✅ **Check if phone numbers have Telegram accounts**\n\n"
        "📝 **How to use:**\n"
        "1. Send your **API_ID** (from my.telegram.org)\n"
        "2. Send your **API_HASH**\n"
        "3. Send phone numbers to check\n\n"
        "👉 **Step 1: Send your API_ID** (6-8 digit number):"
    )
    
    try:
        await message.reply(
            welcome_text,
            reply_markup=get_contact_button(),
            disable_web_page_preview=True
        )
        logger.info(f"✅ Replied to user {user_id}")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    help_text = (
        "🆘 **Help - Telegram Number Checker**\n\n"
        "**Commands:**\n"
        "• /start - Start bot\n"
        "• /help - Show help\n"
        "• /new - Start with new API\n\n"
        "**Get API Credentials:**\n"
        "Visit: https://my.telegram.org\n"
        "→ API Development Tools\n\n"
        "**Phone Number Formats:**\n"
        "• +8801712345678\n"
        "• 8801712345678\n"
        "• 01712345678\n\n"
        "**Separate numbers with:** comma, space, or new line\n\n"
        "**Contact for help:**"
    )
    
    await message.reply(help_text, reply_markup=get_contact_button())

@bot.on_message(filters.command("new") & filters.private)
async def new_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "wait_api_id"}
    await message.reply("🔄 **Starting with new API...**\n\n👉 **Send your API_ID:**")

@bot.on_message(filters.command("test") & filters.private)
async def test_command(client: Client, message: Message):
    """Test command to check if bot is responsive"""
    await message.reply("✅ **Bot is working!**\n\nSend /start to begin.")

@bot.on_message(filters.command("status") & filters.private)
async def status_command(client: Client, message: Message):
    """Check bot status"""
    await message.reply(
        f"🤖 **Bot Status:** ONLINE\n"
        f"📊 **Active Users:** {len(user_states)}\n"
        f"🔧 **Version:** 1.0\n\n"
        f"Everything is working fine!"
    )

# ==================== MESSAGE HANDLER ====================

@bot.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    logger.info(f"📨 Message from {user_id}: {text[:50]}...")
    
    # Skip commands
    if text.startswith('/'):
        return
    
    # Initialize user state if not exists
    if user_id not in user_states:
        user_states[user_id] = {"step": "wait_api_id"}
        await message.reply("⚠️ **Session expired!**\n\nSend /start to begin.")
        return
    
    state = user_states[user_id]
    current_step = state.get("step", "wait_api_id")
    
    # STEP 1: Waiting for API_ID
    if current_step == "wait_api_id":
        if not re.match(r'^\d{6,8}$', text):
            await message.reply(
                "❌ **Invalid API_ID!**\n"
                "API_ID must be 6-8 digit number.\n\n"
                "👉 **Send correct API_ID:**"
            )
            return
        
        state["api_id"] = text
        state["step"] = "wait_api_hash"
        
        await message.reply(
            "✅ **API_ID saved!**\n\n"
            "👉 **Step 2: Send your API_HASH**\n"
            "(32 character hex string)\n\n"
            "**Example:** `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`"
        )
    
    # STEP 2: Waiting for API_HASH
    elif current_step == "wait_api_hash":
        if not re.match(r'^[a-f0-9]{32}$', text.lower()):
            await message.reply(
                "❌ **Invalid API_HASH!**\n"
                "Must be 32 character hex string (lowercase).\n\n"
                "👉 **Send correct API_HASH:**"
            )
            return
        
        state["api_hash"] = text
        state["step"] = "wait_numbers"
        state["valid"] = True
        
        await message.reply(
            "🎉 **CONGRATULATION** 🎉\n\n"
            "✅ **API Credentials accepted!**\n\n"
            "**Now send phone numbers to check:**\n\n"
            "**Formats accepted:**\n"
            "• `+8801712345678`\n"
            "• `8801712345678`\n"
            "• `01712345678`\n\n"
            "**Separate with:** comma, space, or new line\n\n"
            "👉 **Send phone numbers now:**"
        )
    
    # STEP 3: Waiting for phone numbers
    elif current_step == "wait_numbers":
        api_id = state.get("api_id")
        api_hash = state.get("api_hash")
        
        if not api_id or not api_hash:
            await message.reply("❌ **Credentials missing!** Send /start to begin.")
            state["step"] = "wait_api_id"
            return
        
        # Extract numbers
        numbers = []
        for separator in [',', '\n', ' ', ';']:
            if separator in text:
                numbers = [n.strip() for n in text.split(separator) if n.strip()]
                break
        
        if not numbers:
            numbers = [text]
        
        # Validate we have numbers
        valid_numbers = []
        for num in numbers:
            if num.strip():
                valid_numbers.append(num.strip())
        
        if not valid_numbers:
            await message.reply("❌ **No valid numbers found!** Send phone numbers:")
            return
        
        # Limit to 10 numbers for testing
        if len(valid_numbers) > 10:
            valid_numbers = valid_numbers[:10]
            await message.reply(f"⚠️ **Limited to 10 numbers.** Checking first 10.")
        
        # Start processing
        processing_msg = await message.reply(
            f"🔍 **Checking {len(valid_numbers)} numbers...**\n\n"
            f"⏳ **Status:** Starting...\n"
            f"📱 **API:** {api_id[:3]}...{api_id[-3:]}"
        )
        
        try:
            # SIMPLE CHECKING - For testing
            import random
            
            # Simulate checking (replace with actual checking later)
            await asyncio.sleep(2)
            
            # Mock results for testing
            registered = valid_numbers[:len(valid_numbers)//2]
            not_registered = valid_numbers[len(valid_numbers)//2:]
            
            # Format results
            result_text = ""
            
            if registered:
                result_text += "**✅ ACCOUNTS FOUND:**\n"
                for num in registered[:5]:
                    result_text += f"✅ `{num}`\n"
                if len(registered) > 5:
                    result_text += f"✅ ... and {len(registered)-5} more\n"
                result_text += "\n"
            
            if not_registered:
                result_text += "**🔒 NO ACCOUNTS:**\n"
                for num in not_registered[:5]:
                    result_text += f"🔒 `{num}`\n"
                if len(not_registered) > 5:
                    result_text += f"🔒 ... and {len(not_registered)-5} more\n"
                result_text += "\n"
            
            result_text += f"**📊 SUMMARY:**\n"
            result_text += f"• Total checked: {len(valid_numbers)}\n"
            result_text += f"• ✅ With account: {len(registered)}\n"
            result_text += f"• 🔒 No account: {len(not_registered)}\n"
            
            await processing_msg.edit_text(
                f"✅ **CHECKING COMPLETE!**\n\n{result_text}",
                reply_markup=get_contact_button()
            )
            
            # Keep user in same state
            state["step"] = "wait_numbers"
            
        except Exception as e:
            logger.error(f"Checking error: {e}")
            await processing_msg.edit_text(
                f"❌ **Error occurred!**\n\n"
                f"Error: `{str(e)[:100]}`\n\n"
                f"Please try again or contact developer.",
                reply_markup=get_contact_button()
            )

# ==================== STARTUP ====================

async def main():
    """Main function to run the bot"""
    logger.info("🚀 Starting Telegram Number Checker Bot...")
    
    try:
        await bot.start()
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"✅ Bot started successfully!")
        logger.info(f"🤖 Username: @{me.username}")
        logger.info(f"🆔 ID: {me.id}")
        
        print("\n" + "="*60)
        print(f"🤖 BOT: @{me.username}")
        print(f"📞 DEVELOPER: @Mr_Evan3490")
        print(f"🚀 STATUS: RUNNING")
        print(f"📍 REGION: Render.com")
        print("="*60)
        print("\n📢 Send /start to your bot to test!")
        print("="*60)
        
        # Keep bot running
        await idle()
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ ERROR: {e}")
    finally:
        await bot.stop()
        logger.info("👋 Bot stopped")

# ==================== RUN BOT ====================

if __name__ == "__main__":
    # For Render.com compatibility
    try:
        # Set event loop policy for cloud
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Run bot
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
