# Telegram Number Checker Bot

A Telegram bot to check if phone numbers have Telegram accounts.

## Features
- Check multiple phone numbers at once
- Bangladeshi number format support
- Step-by-step user interface
- Contact developer button

## Deployment on Railway.app

### 1. Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Get $5 free credit

### 2. Deploy Bot
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your repository
4. Railway will auto-deploy

### 3. Set Environment Variables
In Railway dashboard, add these variables:
- `API_ID`: From my.telegram.org
- `API_HASH`: From my.telegram.org
- `BOT_TOKEN`: From @BotFather

### 4. Test Bot
1. Check logs for "Bot started successfully!"
2. Go to Telegram
3. Search for your bot
4. Send `/start`

## Credentials Setup

### Get Bot Token:
1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Choose bot name
4. Get `BOT_TOKEN`

### Get API ID & Hash:
1. Visit: https://my.telegram.org
2. Login with phone number
3. Go to "API Development Tools"
4. Create app
5. Get `API_ID` and `API_HASH`

## Usage
1. Send `/start` to bot
2. Enter your API_ID
3. Enter your API_HASH
4. Enter phone numbers to check
5. Get results with ✅ (registered) and 🔒 (not registered)

## Contact
Developer: [@Mr_Evan3490](https://t.me/Mr_Evan3490)
