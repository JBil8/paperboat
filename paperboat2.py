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

from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, Updater, Job, filters, CallbackQueryHandler


from keys import TELEGRAM_KEY_DEV
from telegram import ReplyKeyboardMarkup

# for database
import sqlite3
from cryptography.fernet import Fernet

# Define predefined options
options = ['Bio', 'Photonics', 'Chemistry', 'Energy & Materials']


path = os.getcwd() + '/'

# Initialize Fernet key
with open(path + 'cripto_bot.txt', 'rb') as filekey:
    key = filekey.read()
fernet = Fernet(key)


def initialize_database():
    path = os.getcwd() + '/'
    db_path = path + 'users_preferences.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users_preferences (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            preferences TEXT
        )
    ''')
    conn.commit()
    conn.close()

initialize_database()


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def retrieve_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieve and decrypt user preferences."""
    chat_id = update.message.chat_id

    conn = sqlite3.connect('users_preferences.db')
    c = conn.cursor()
    c.execute("SELECT preferences FROM users_preferences WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()

    if row and row[0]:
        encrypted_preferences = row[0]
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        preferences_list = decrypted_preferences.split(',')
        await update.message.reply_text(f"Your preferences are: {preferences_list}")
    else:
        await update.message.reply_text("You haven't set any preferences yet.")
    conn.close()

async def send_preference_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with preference options as inline buttons."""
    chat_id = update.message.chat_id
    action = 'add' if 'add' in update.message.text else 'remove'
    keyboard = []
    available_preferences = ['Bio', 'Photonics', 'Chemistry', 'Energy & Materials']

    # Connect to the database and fetch current preferences
    conn = sqlite3.connect('users_preferences.db')
    c = conn.cursor()
    c.execute("SELECT preferences FROM users_preferences WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    current_preferences = []

    if row and row[0]:
        encrypted_preferences = row[0]
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        current_preferences = decrypted_preferences.split(',')

    # Create a button for each preference
    for preference in available_preferences:
        if (action == 'add' and preference not in current_preferences) or (action == 'remove' and preference in current_preferences):
            callback_data = f"{action}_{preference}"
            button_text = f"{'Add' if action == 'add' else 'Remove'} {preference}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an option:", reply_markup=reply_markup)
    conn.close()

async def update_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, preference: str):
    """Update user preferences by adding or removing based on inline button presses."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query first
    chat_id = query.from_user.id

    # Connect to the database and fetch current preferences
    conn = sqlite3.connect('users_preferences.db')
    c = conn.cursor()
    c.execute("SELECT preferences FROM users_preferences WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    preferences_list = []

    if row and row[0]:
        encrypted_preferences = row[0]
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        preferences_list = decrypted_preferences.split(',')

    # Perform the add or remove action
    updated = False
    if action == 'add' and preference not in preferences_list:
        preferences_list.append(preference)
        updated = True
    elif action == 'remove' and preference in preferences_list:
        preferences_list.remove(preference)
        updated = True

    if updated:
        encrypted_preferences = fernet.encrypt(','.join(preferences_list).encode()).decode()
        c.execute("UPDATE users_preferences SET preferences = ? WHERE chat_id = ?", (encrypted_preferences, chat_id))
        conn.commit()
        await set_callback(update, context)
        message = f"{'Added' if action == 'add' else 'Removed'} {preference} to your preferences."
    else:
        message = "No changes made to your preferences."

    await query.edit_message_text(text=message)
    conn.close()

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline buttons."""
    callback_data = update.callback_query.data
    action, preference = callback_data.split('_')
    
    # Directly call the asynchronous function with await
    await update_preferences(update, context, action, preference)

async def handle_selected_topic(update, context):
    selected_topic = update.message.text
    # Process the selected topic here
    await update.message.reply_text(f"You selected: {selected_topic}")

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
    """Send a message when the command /start is issued and register the user."""
    user = update.effective_user
    chat_id = update.message.chat_id
    username = user.username

    conn = sqlite3.connect('users_preferences.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users_preferences (chat_id, username) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET username=excluded.username;
    ''', (chat_id, username))
    conn.commit()
    conn.close()

    await update.message.reply_html(
        rf"Hi {user.mention_html()}! Welcome to PaperBoat, the place to get up to date with current scientific literature in your field!",
        reply_markup=ForceReply(selective=True),
    )

async def set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    job_interval = 60  # seconds

    # Check and remove any existing job
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
        del context.chat_data['job']

    # Schedule a new job
    new_job = context.job_queue.run_repeating(
        give_text, interval=job_interval, first=1, chat_id=chat_id, name=str(chat_id)
    )
    context.chat_data['job'] = new_job

    # Respond to the user
    if update.effective_message:
        await update.effective_message.reply_text("You will now receive daily updates!")
    else:
        logger.info("set_callback triggered without effective_message.")

async def stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a job from the queue."""
    chat_id = update.effective_message.chat_id

    # Retrieve the job from chat_data and stop it
    job = context.chat_data.get('job')
    if job:
        job.schedule_removal()
        await update.message.reply_text("You will no longer receive daily updates.")
        del context.chat_data['job']  # Remove the job from chat_data
    else:
        await update.message.reply_text("No active subscription found.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    #need to implement this
    await update.message.reply_text("Help! We are currently working on this feature.")

async def give_text(context: ContextTypes.DEFAULT_TYPE) -> None:
    #chat_id = context.job.context  # Here, context is the chat_id passed to run_repeating

    chat_id = context.job.chat_id
    # Connect to the database
    conn = sqlite3.connect(os.path.join(os.getcwd(), 'users_preferences.db'))
    c = conn.cursor()

    c.execute("SELECT preferences FROM users_preferences WHERE chat_id = ?", (chat_id,))

    result = c.fetchone()
    if result is None:
        await context.bot.send_message(chat_id=chat_id, text="You have not set any preferences.")
        return

    encrypted_preferences = result[0]
    decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
    users_preferences = decrypted_preferences.split(',')

    # Initialize an empty string to store the message text
    message_text = ""

    # Import today.csv
    csv_file_path = 'today.csv'

    # Open the CSV file in read mode
    with open(csv_file_path, 'r') as file:
        csv_reader = csv.reader(file, delimiter=',')
        for row in csv_reader:
            category = row[4]  # Assuming the category is in the 5th column
            if category in users_preferences:
                name = row[1]  # Assuming the name is in the 2nd column
                url = row[5]  # Assuming the URL is in the 6th column
                message_text += f"<a href='{url}'>{name}</a>\n"

    if not message_text:
        await context.bot.send_message(chat_id=chat_id, text="No papers found for your preferences today.")
        return

    # Send the message text with hyperlinks using the Telegram bot
    chunked_text = partition_string(message_text)
    for chunk in chunked_text:
        await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='HTML')


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_KEY_DEV).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))


    application.add_handler(CommandHandler("retrieve_preferences", retrieve_preferences))

    # Schedule the job to run 
    application.add_handler(CommandHandler("send_daily", set_callback))
    # Stop the job (daily updates)
    application.add_handler(CommandHandler("stop_daily", stop_callback))

    # Register the callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))

        # Command handler for initiating the addition of preferences
    application.add_handler(CommandHandler("add_preference", send_preference_options))

    # Command handler for initiating the removal of preferences
    application.add_handler(CommandHandler("remove_preference", send_preference_options))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    

if __name__ == "__main__":
    main()  