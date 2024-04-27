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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def retrieve_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieve and decrypt user preferences."""
    username = update.effective_user.username

    # Retrieve preferences from the database
    c.execute("SELECT preferences FROM user_preferences WHERE username = ?", (username,))
    row = c.fetchone()
    if row:
        encrypted_preferences = row[0]
        # Decrypt preferences
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        preferences_list = decrypted_preferences.split(',')
        await update.message.reply_text(f"Your preferences are: {preferences_list}")
    else:
        await update.message.reply_text("You haven't set any preferences yet.")

async def send_preference_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with preference options as inline buttons."""
    # Determine the action based on the command used
    action = 'add' if 'add' in update.message.text else 'remove'
    username = update.effective_user.username
    keyboard = []

    # Define the available preferences
    available_preferences = ['Bio', 'Photonics', 'Chemistry', 'Energy & Materials']

    # Fetch current preferences from the database
    c.execute("SELECT preferences FROM user_preferences WHERE username = ?", (username,))
    row = c.fetchone()
    current_preferences = []

    if row:
        encrypted_preferences = row[0]
        decrypted_preferences = fernet.decrypt(encrypted_preferences.encode()).decode()
        current_preferences = decrypted_preferences.split(',')

    # Create a button for each preference
    for preference in available_preferences:
        if (action == 'add' and preference not in current_preferences) or (action == 'remove' and preference in current_preferences):
            callback_data = f"{action}_{preference}"  # Format: "add_Bio" or "remove_Bio"
            button_text = f"{'Add' if action == 'add' else 'Remove'} {preference}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an option:", reply_markup=reply_markup)

async def update_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, preference: str):
    """Update user preferences by adding or removing based on inline button presses."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query first
    username = query.from_user.username

    # Fetch current preferences
    c.execute("SELECT preferences FROM user_preferences WHERE username = ?", (username,))
    row = c.fetchone()
    preferences_list = []

    if row:
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

    # Send confirmation message
    if updated:
        message = f"{'Added' if action == 'add' else 'Removed'} {preference} to your preferences."
        encrypted_preferences = fernet.encrypt(','.join(preferences_list).encode()).decode()
        c.execute("INSERT OR REPLACE INTO user_preferences (username, preferences) VALUES (?, ?)", (username, encrypted_preferences))
        conn.commit()
        await set_callback(update, context)
    else:
        message = "No changes made to your preferences."

    await query.edit_message_text(text=message)


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
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()} welcome to PaperBoat, the place to get up to date with current scientific literature in your field!",
        reply_markup=ForceReply(selective=True),
    )

# async def set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Add a job to the queue."""
#     chat_id = update.effective_message.chat_id
#     job_interval = 60  # seconds

#     # Check if a job already exists and remove it
#     current_job = context.chat_data.get('job')
#     if current_job is not None:
#         current_job.schedule_removal()

#     # Schedule a new job
#     new_job = context.job_queue.run_repeating(give_text, chat_id=chat_id, interval=job_interval, first=1)
#     context.chat_data['job'] = new_job  # Store the job object in chat_data

#     await update.message.reply_text("You will now receive daily updates!")

async def set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
        # Check if a job already exists and remove it
    current_job = context.chat_data.get('job')
    if current_job is not None:
        current_job.schedule_removal()

    username = update.effective_user.username  # Get the username
    job_data = {'chat_id': chat_id, 'username': username}

    # Schedule a job with user-specific context
    new_job = context.job_queue.run_repeating(
        give_text, interval=60, first=1, context=job_data
    )
    context.chat_data['job'] = new_job  # Store the job object in chat_data
    await update.message.reply_text("You will now receive daily updates!")

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
    """
    Send titles and link of papers published today from today.csv
    """   

    username = context.job.context

    # Initialize an empty string to store the message text
    message_text = ""

    #import today.csv
    csv_file_path = 'today.csv'
    
    #open database
    conn = sqlite3.connect(path + 'user_preferences.db')
    c = conn.cursor()

    #find the username in the csv file and check the fith column for the preferences
    # Fetch user preferences from the database using chat_id
    c.execute("SELECT preferences FROM users_preferences WHERE username = ?", (username,))
    result = c.fetchone()

    result = c.fetchone()
    if not result:
        await context.bot.send_message(chat_id=chat_id, text="You have not set any preferences.")
        return


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