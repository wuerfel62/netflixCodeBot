Collecting workspace information```markdown
# Netflix Code Bot

This project is a Python-based Discord bot that automates the process of retrieving Netflix verification codes from emails and sending them to a specified Discord channel. It uses IMAP to access emails, extracts verification links or codes, and posts them to Discord.

## Features
- Connects to an email inbox via IMAP to fetch unread emails.
- Filters emails based on a specific subject line.
- Extracts Netflix verification links or codes from the email content.
- Sends the extracted code to a specified Discord channel.
- Configurable via a `.env` file for secure and flexible setup.

## Requirements
- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

## Installation and Setup

### Step 1: Clone the Repository
Clone the repository to your local machine:
```bash
git clone <repository-url>
cd netflixCodeBot
```

### Step 2: Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Step 3: Configure the Environment
Create a `.env` file in the root directory of the project and add the following variables:
```
IMAP_SERVER=imap.your-email-provider.com
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-email-password
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=your-discord-channel-id
SUBJECT_FILTER=Ihr zeitlich begrenzter Zugangscode
POLL_INTERVAL=30
```
- Replace `your-email-provider.com`, `your-email@example.com`, and `your-email-password` with your email provider's IMAP server, your email address, and your email password, respectively.
- Replace `your-discord-bot-token` with the token of your Discord bot.
- Replace `your-discord-channel-id` with the ID of the Discord channel where the bot should send messages.
- Adjust `SUBJECT_FILTER` to match the subject line of the emails you want to process.
- Set `POLL_INTERVAL` to define how often (in seconds) the bot should check for new emails.

### Step 4: Run the Bot
Start the bot by running the following command:
```bash
python DiscordCodeBotv2.py
```

### Step 5: Invite the Bot to Your Discord Server
- Go to the Discord Developer Portal and generate an OAuth2 URL for your bot with the necessary permissions.
- Use the URL to invite the bot to your server.

## Notes
- Ensure that the `.env` file is included in `.gitignore` to prevent sensitive information from being pushed to version control.
- The bot requires permission to send messages in the specified Discord channel.

## Troubleshooting
- If the bot fails to connect to your email server, verify your IMAP settings and credentials.
- If the bot cannot send messages to Discord, ensure it has the necessary permissions in the target channel.