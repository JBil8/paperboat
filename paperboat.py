#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Development version of the PaperBoat bot.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:

```python
python paperboat.py
```

Press Ctrl-C on the command line to stop the bot.

"""

import logging
import csv
import os

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, Updater, Job, filters


from keys import TELEGRAM_KEY_DEV
from telegram import ReplyKeyboardMarkup

# for database
import sqlite3
from cryptography.fernet import Fernet

#for automatic scraping
# import requests
# from bs4 import BeautifulSoup
# import datetime

#from automatic_scraper import get_text, set_day, set_url #, query

path = os.getcwd() + '/'

# Initialize Fernet key
with open(path + 'cripto_bot.txt', 'rb') as filekey:
    key = filekey.read()
fernet = Fernet(key)

# Create or connect to the SQLite database
conn = sqlite3.connect(path + 'user_preferences.db')
c = conn.cursor()

# Create a table to store user preferences if it doesn't exist
c.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        username TEXT PRIMARY KEY,
        preferences TEXT
    )
''')
conn.commit()

async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user preferences."""
    # Extract username and preferences from the message
    username = update.effective_user.username
    preferences = update.message.text.split()  # Assuming preferences are provided as space-separated values
    print(preferences)
    # Encrypt preferences
    encrypted_preferences = fernet.encrypt(','.join(preferences).encode()).decode()

    # Store username and encrypted preferences in the database
    c.execute("INSERT OR REPLACE INTO user_preferences (username, preferences) VALUES (?, ?)",
              (username, encrypted_preferences))
    conn.commit()

    await update.message.reply_text("Your preferences have been saved!")

async def retrieve_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieve and decrypt user preferences."""
    # Extract username from the message
    username = update.effective_user.username

    # Retrieve preferences from the database
    c.execute("SELECT preferences FROM user_preferences WHERE username = ?", (username,))
    row = c.fetchone()
    if row:
        encrypted_preferences = row[0]
        # Decrypt preferences
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        print(decrypted_preferences)
        preferences_list = decrypted_preferences.split(',')
        await update.message.reply_text(f"Your preferences are: {preferences_list}")
    else:
        await update.message.reply_text("You haven't set any preferences yet.")

# Define predefined options
options = ['Bio', 'Photonics', 'Chemistry', 'Energy & Materials']

async def set_topic(update, context):
    reply_markup = ReplyKeyboardMarkup([options], one_time_keyboard=True)
    await update.message.reply_text("Please select a topic:", reply_markup=reply_markup)
    # save the selected topic in the user's context
    context.user_data['selected_topic'] = True
    
async def handle_selected_topic(update, context):
    selected_topic = update.message.text
    # Process the selected topic here
    await update.message.reply_text(f"You selected: {selected_topic}")


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.

def partition_string(message):
    max_length = 4096
    lines = message.split("\n")
    partitions = []
    current_partition = ""

    for line in lines:
        if len(current_partition + line) <= max_length:
            current_partition += line + "\n"
        else:
            partitions.append(current_partition)
            current_partition = line + "\n"

    if current_partition:
        partitions.append(current_partition)

    return partitions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()} welcome to PaperBoat, the place to get up to date with current scientific literature in your field!",
        reply_markup=ForceReply(selective=True),
    )

async def set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id #get chat id dynamically
    job_interval = 60 # seconds
    context.job_queue.run_repeating(give_text, chat_id=chat_id, interval=job_interval, first=1)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    #need to implement this
    await update.message.reply_text("Help! We are currently working on this feature.")

async def give_text(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send titles and link of papers published today from today.csv
    """
    # Initialize an empty string to store the message text
    message_text = ""

    #import today.csv
    csv_file_path = 'today.csv'

    # Open the CSV file in read mode
    with open(csv_file_path, 'r') as file:
        # Create a CSV reader object
        csv_reader = csv.reader(file, delimiter=',')
        
         # Iterate over each row in the CSV file
        for row in csv_reader:
            # Assuming the first column contains names and the second column contains URLs
            name = row[1]
            url = row[5]
            
            # Append the formatted HTML string to the message text
            message_text += f"<a href='{url}'>{name}</a>\n"
    
    # Send the message text with hyperlinks using the Telegram bot
    chunked_text = partition_string(message_text)
    for chunk in chunked_text:
        await context.bot.send_message(chat_id=context.job.chat_id, text=chunk, parse_mode='HTML')
    

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_KEY_DEV).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    #application.add_handler(CommandHandler("journal_text", give_text))
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, give_text))

    application.add_handler(CommandHandler("set_preferences", handle_preferences))
    application.add_handler(CommandHandler("retrieve_preferences", retrieve_preferences))

    application.add_handler(CommandHandler("set_topic", set_topic))

    #application.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_selected_topic))

    # Schedule the job to run 
    application.add_handler(CommandHandler("send_daily", set_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()  