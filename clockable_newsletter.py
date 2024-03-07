import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from cryptography.fernet import Fernet
import sqlite3
import pandas as pd
import numpy as np

# users' data
sender_email = "paperboatepfl@gmail.com"

with open('gmailpaperbotlogin.txt', 'r') as file:
    password = file.read().strip()

### update the database checking if there are new logins from the Google form
# use creds to create a client to interact with the Google Drive API
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# find the workbook by name and open the first sheet
sheet = client.open("paperbot").sheet1

# extract all of the records for the data in the sheet
list_of_hashes = sheet.get_all_records()
list_of_hashes_optout = [entry for entry in list_of_hashes if entry['Why are you here?'] == 'Opt out']
list_of_hashes = [entry for entry in list_of_hashes if entry['Why are you here?'] == 'Sign up']

# load criptographic key
with open('criptokey.txt', 'rb') as filekey:
    key = filekey.read()

fernet = Fernet(key)

# open database
conn = sqlite3.connect('email_subscribers.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS subscribers
             (user TEXT, field TEXT)''')
conn.commit()
conn.close()

#### update database: google sheet -> SQL db with encrypted data
def encrypt_and_update_database(list_of_hashes):
    conn = sqlite3.connect('email_subscribers.db')
    c = conn.cursor()
    for item in list_of_hashes:
        if item['Consent'] == 'I agree to receive Paperboat daily updates': 
            encrypted_email = fernet.encrypt(item['Your email address'].encode())
            encrypted_field = fernet.encrypt(item['Your field of interest'].encode())
            c.execute("INSERT INTO subscribers (user, field) VALUES (?, ?)",
                      (encrypted_email, encrypted_field))
    conn.commit()
    conn.close()

encrypt_and_update_database(list_of_hashes)

#### !!!!!!!!!!!!!!! remove duplicates, remove optouts after encrypting them
#### !!!!!!!!!!!!!!! remove ALL stuff that is already in the db from the excel

#### decrypt
conn = sqlite3.connect('email_subscribers.db')
c = conn.cursor()

c.execute("SELECT user, field FROM subscribers")
encrypted_data = c.fetchall()

decrypted_data = []

for row in encrypted_data:
    decrypted_email = fernet.decrypt(row[0]).decode()
    decrypted_field = fernet.decrypt(row[1]).decode()
    decrypted_data.append((decrypted_email, decrypted_field))

conn.close()

file_contentFULL = pd.read_csv("today.csv")

for i in range(0,len(decrypted_data)):
    
    receiver_email = decrypted_data[i][0]
    receiver_topic = decrypted_data[i][1]
    
    html_content = """
    <html>
    <head>
        <style>
            body {font-family: Arial, sans-serif; margin: 20px;}
            h2 {color: #336699;}
            ul {color: #555555;}
            li {margin: 5px 0;}
        </style>
    </head>
    <body>
        <h1>Welcome to your daily PaperBoat!</h1>
    """
    file_content = file_contentFULL[file_contentFULL['Field'] == receiver_topic]
    
    for journal_name in file_content['Journal'].unique():
        journal_df = file_content[file_content['Journal'] == journal_name]
        
        html_content += f"<h2>{journal_name}</h2><ul>"
        
        for index, row in journal_df.iterrows():
            title = row['Title'].strip()
            link = row['Link'].strip()
            if title:  
                html_content += f'<li><a href="{link}">{title}</a></li>'
        
        html_content += "</ul>"
    html_content += """
        <p>Have a wonderful day!</p>
        <p>Your PaperBoat Team at EPFL</p>
    </body>
    </html>
    """
    
    #### prepare message
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Daily PaperBoat Digest"
    
    #  HTML content
    part = MIMEText(html_content, "html")
    message.attach(part)
    text = message.as_string()
    
    # sending the email
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, text)
    
    ### TODO: send this message to multiple outputs so i can see if a mess is happening
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()