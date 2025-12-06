# Telegram Number Checker Bot

A Telegram bot that checks if phone numbers have Telegram accounts.

## Features
- Check multiple phone numbers at once
- Real-time validation of API credentials
- Simple step-by-step interface
- Bangladeshi number format support
- Contact developer button

## Setup

### 1. Create a Telegram Bot
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose a name for your bot
4. Choose a username (must end with 'bot')
5. Copy the **BOT_TOKEN**

### 2. Local Development
```bash
# Clone/download files
# Create .env file with:
BOT_TOKEN=your_token_from_botfather

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot.py
