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

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, Updater, Job
from keys import TELEGRAM_KEY_DEV

#for automatic scraping
import requests
from bs4 import BeautifulSoup
import datetime

from automatic_scraper import get_text, set_day, set_url #, query

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()} welcome to PaperBoat, the place to get up to date with current scientific literature in your field!",
        reply_markup=ForceReply(selective=True),
    )

# async def callback_minute(update: Updater ,context: ContextTypes.DEFAULT_TYPE):
#     #await context.bot.send_message(chat_id='385856535', text='One message every 10 seconds')
#     job = context.job
#     # Get the update from the context
#     update = context.job.context['update']
#     #await context.bot.send_message(chat_id=job.chat_id, text='One message every 10 seconds')
#     await give_text(context)

async def set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id #get chat id dynamically
    job_interval = 10 # seconds
    context.job_queue.run_repeating(give_text, chat_id=chat_id, interval=job_interval, first=1)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    #need to implement this
    await update.message.reply_text("Help! We are currently working on this feature.")

async def give_text(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the text from the journal"""
    #journal = update.message.text
    journal = "biorxiv"
    day = set_day()
    url = set_url(str(journal))
    print(context.job.chat_id)
    await context.bot.send_message(chat_id=context.job.chat_id, text=get_text(url))


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_KEY_DEV).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    #application.add_handler(CommandHandler("journal_text", give_text))
    #application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, give_text))

    # Schedule the job to run 
    application.add_handler(CommandHandler("send_daily", set_callback))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()  