############ CURRENT CRONTAB SCRIPT IS STORED ON MY MAC; open with crontab -e (MAC VERSION!)
# content: 
#00 21 * * * . /Users/fusar/anaconda3/etc/profile.d/conda.sh; conda activate tutorial-llm-api; /Users/fusar/anaconda3/envs/tutorial-llm-api/bin/python #/Users/fusar/MINIHACKATHON_TUTORIALS/clockable_newsletter.py  >> /Users/fusar/logfile.log 2>&1




############ ENGINE [BIOLOGY ONLY HERE]


import pandas as pd
import requests
import os
import re
import random
import json
import datetime
from bs4 import BeautifulSoup
import numpy as np
import scipy
import matplotlib.pyplot as plt
import openai
import pandas as pd
import time
import datetime
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#import keys #############


############# TAKE CARE!

#importing links to all journals
links = pd.read_csv("paperboat_linksBIOLOGY.csv")
badjournals = ['Advances in Applied Energy',
 'Nano Energy',
 'Applied Energy',
 'Energy Strategy Reviews',
 'Materials Today Energy',
 'Energy',
 'ISPRS Journal of Photogrammetry and Remote Sensing',
 'Materials Today Physics',
 'AVS Quantum Science',
 'Journal of Energy Chemistry',
 'Nature Protocols',
 'Autophagy']

### for prototyping 
links = links.iloc[22:27,:]

today = str(datetime.date.today())

# OpenAI API key
client = openai.OpenAI(api_key= "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") #keys.OPENAI_KEY    #############

def safe_api_call(call_function, *args, **kwargs):
    while True:
        try:
            return call_function(*args, **kwargs)
        except openai.error.RateLimitError as e:

            match = re.search(r'Please try again in (\d+(\.\d+)?)s.', str(e))
            if match:
                wait_time = float(match.group(1)) + 1  
                print(f"Rate limit reached, waiting for {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                raise

# Initializing the dataframe to store all data
combined_df = pd.DataFrame(columns=["Title", "Date", "Journal", "Field"])

from datetime import datetime

for i in range(0,links.shape[0]):

    print(np.array(links['Journal'])[i])
    
    url = np.array(links['Link'])[i]
    journal = np.array(links['Journal'])[i]
    field = np.array(links['Topic/Field'])[i]
    
    response = requests.get(url).text 
    soup = BeautifulSoup(response, 'html.parser')
    titles = str(soup.get_text().replace("\n\n", " ")) ##### for the limit on gpt4
    
    badj = np.array(links['Journal'])[i] in badjournals
    condition = (titles == 'Just a moment...Enable JavaScript and cookies to continue') | badj
    
    if condition:
        print("in")
        options = Options()
        options.headless = True 
        path_to_chromedriver = '/Users/fusar/Downloads/chromedriver-mac-arm64/chromedriver'
        service = Service(executable_path=path_to_chromedriver)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)
        page_content = driver.page_source
        driver.quit()
        soup = BeautifulSoup(page_content, 'html.parser')
        titles = str(soup.get_text().replace("\n\n", " "))

    max_context_length = 4096 * 8 ### reasonable heuristic

    for k in range(math.ceil(len(titles) / max_context_length)):
        try:
            print(k)
            extracted_titles = []

            start_idx = k * max_context_length
            end_idx = min((k + 1) * max_context_length, len(titles))

            current_titles = titles[start_idx:end_idx]


            response = safe_api_call(
                client.chat.completions.create,
                model="gpt-3.5-turbo-0125", ###############
                messages=[{
                    "role": "user", 
                    "content": ("Extract paper TITLES from this text. "
                                "For example, for  'November 2, 2023 |"
        "https://doi.org/10.1371/journal.pgen.1011021    Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics   "          
        "              Luke N. Yaeger,              Shawn French,              Eric D. Brown,              Jean Philippe Côté,              Lori L. Burrows        "
        "PLOS Genetics: published' you will return """"Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"""""
                                "Never return this very same title """"Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"""""
                                "Return one title per line. DO NOT MISS ANY TITLE. We are dealing with scientific "
                                "paper titles, so return only what's reasonable (e.g., something like "
                                "'Clinical Trials', 'Developmental Biology', 'Ecology' is likely NOT a title "
                                "of a paper, it's too generic). Just return the PLAUSIBLE titles. do NOT format "
                                "with dashes or numbers, just plain titles. remember, it's IMPERATIVE "
                                "that you change line between subsequent titles!\n\n\n"
     + current_titles)
                }]
            )

            extracted_titles.extend(response.choices[0].message.content.split('\n'))

            df = pd.DataFrame(extracted_titles, columns=["Title"])
            df['Date'] = datetime.today().strftime('%Y-%m-%d')
            df['Journal'] = journal
            df['Field'] = field
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e: 
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

            with open('log_errors.txt', 'a') as log_file:
                log_file.write(f"{formatted_time} - Error: {str(e)}\n")
            continue
            
combined_df = combined_df[combined_df['Title'].apply(lambda x: len(x.split()) > 6)].drop_duplicates()

#!pip install requests==2.14.2 ####################

sss = combined_df['Title']

res = []

import requests

res = []

for s in sss:
    try:
        url = "https://search.yahoo.com/search?p=SUBSTITUTED"
        modified_s = s.replace(" ", "+")
        url = url.replace("SUBSTITUTED", modified_s)
        options = Options()
        options.headless = True 
        path_to_chromedriver = '/Users/fusar/Downloads/chromedriver-mac-arm64/chromedriver'
        service = Service(executable_path=path_to_chromedriver)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)
        first_result_link = driver.find_element("css selector", "a[data-matarget='algo']")
        link = first_result_link.get_attribute('href')
        #print(link)
        res.append(link)
        driver.quit()
    except:
        res.append('Failed')

combined_df['Link'] = res
full_df = pd.read_hdf("full_df.h5ad", key="table")
full_df = full_df.loc[:, [x!="Unnamed: 0" for x in full_df.columns]]
combined_df = combined_df.loc[~combined_df['Title'].isin(full_df['Title']),:]

combined_df.to_csv("today.csv")
full_df = pd.concat([full_df, combined_df], axis=0)
full_df = full_df.drop_duplicates()
full_df.to_hdf("full_df.h5ad", key="table")














########################################################################################################################

############ NEWSLETTER


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from cryptography.fernet import Fernet
import sqlite3
import pandas as pd
import numpy as np
import datetime
import hashlib

# users' data
sender_email = "paperboatepfl@gmail.com"
PATH = '/Users/fusar/MINIHACKATHON_TUTORIALS/'

with open(PATH+'gmailpaperbotlogin.txt', 'r') as file:
    password = file.read().strip()

### update the database checking if there are new logins from the Google form
# use creds to create a client to interact with the Google Drive API
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(PATH+'client_secret.json', scope)
client = gspread.authorize(creds)

# find the workbook by name and open the first sheet
sheet = client.open("paperbot").sheet1

# extract all of the records for the data in the sheet
list_of_hashes = sheet.get_all_records()
list_of_hashes_optout = [entry for entry in list_of_hashes if entry['Why are you here?'] == 'Opt out (only if you signed up before)']
list_of_hashes = [entry for entry in list_of_hashes if entry['Why are you here?'] == 'Sign up']

# load criptographic key
with open(PATH+'criptokey.txt', 'rb') as filekey:
    key = filekey.read()

fernet = Fernet(key)

# open database
conn = sqlite3.connect(PATH + 'email_subscribers.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user TEXT, 
        field TEXT,
        UNIQUE(user, field)
    )
''')
conn.commit()

try:
    c.execute("ALTER TABLE subscribers ADD COLUMN pair_hash TEXT")
    conn.commit()
except sqlite3.OperationalError as e:
    print("An error occurred:", e)

def encrypt_and_update_database(list_of_hashes, sheet):
    conn = sqlite3.connect(PATH + 'email_subscribers.db')
    c = conn.cursor()
    row_number = 2  # Assuming first row is header in Google Sheets
    for item in list_of_hashes:
        if item['Consent'] == 'I agree to receive Paperboat daily updates':
            encrypted_email = fernet.encrypt(item['Your email address'].encode())
            encrypted_field = fernet.encrypt(item['Your field of interest'].encode())
            pair_hash = generate_hash_for_pair(item['Your email address'], item['Your field of interest'])

            try:
                c.execute("INSERT OR IGNORE INTO subscribers (user, field, pair_hash) VALUES (?, ?, ?)",
                          (encrypted_email, encrypted_field, pair_hash))
                if c.rowcount > 0:  # If the row was inserted, delete from sheet
                    sheet.delete_rows(row_number)
                else:
                    row_number += 1  # Only increment if row wasn't deleted
            except sqlite3.IntegrityError:
                row_number += 1  # Skip duplicate
    conn.commit()
    conn.close()

def backup_database_if_required():
    today = datetime.datetime.now()
    if today.day == 16:
        conn = sqlite3.connect(PATH + 'email_subscribers.db')
        backup_conn = sqlite3.connect(PATH + f'email_subscribers_backup_{today.strftime("%Y%m%d")}.db')
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()

def generate_hash_for_pair(email, field):
    pair_string = f"{email.lower()}|{field}".encode() 
    return hashlib.sha256(pair_string).hexdigest()

def remove_opt_outs(list_of_hashes_optout):
    conn = sqlite3.connect(PATH + 'email_subscribers.db')
    c = conn.cursor()
    for item in list_of_hashes_optout:
        pair_hash = generate_hash_for_pair(item['Your email address'], item['Your field of interest'])
        c.execute("DELETE FROM subscribers WHERE pair_hash = ?", (pair_hash,))
    conn.commit()
    conn.close()
        
# Execute your functions
backup_database_if_required()
encrypt_and_update_database(list_of_hashes, sheet)
remove_opt_outs(list_of_hashes_optout)

#### decrypt
conn = sqlite3.connect(PATH+'email_subscribers.db')
c = conn.cursor()

delete_sql = """
WITH RankedSubscribers AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY user, field ORDER BY rowid) as rn
  FROM subscribers
)
DELETE FROM subscribers
WHERE rowid IN (
  SELECT rowid FROM RankedSubscribers WHERE rn > 1
);

"""

try:
    c.execute(delete_sql)
    conn.commit()
except sqlite3.Error as e:
    print("An error occurred:", e)

c.execute("SELECT user, field FROM subscribers")
encrypted_data = c.fetchall()

decrypted_data = []

for row in encrypted_data:
    decrypted_email = fernet.decrypt(row[0]).decode()
    decrypted_field = fernet.decrypt(row[1]).decode()
    decrypted_data.append((decrypted_email, decrypted_field))
    decrypted_data = list(set(decrypted_data)) ### keep unique

conn.close()

file_contentFULL = pd.read_csv(PATH+"today.csv")
file_contentFULL['Field'][file_contentFULL['Field'] == "Bio"] = "Biological sciences"

for i in range(0,len(decrypted_data)): #### BCC? per topic | oppure una mail unica per utente? # o si può mandare tante mails in parallelo?
    
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
        
    link = "https://forms.gle/hjsHK6vcQqsqT2Cr6"
    title = "Do you like Paperboat? Use this link to share it with your community!"
    html_content += f'<li><a href="{link}">{title}</a></li>'
 
    link = "https://forms.gle/hjsHK6vcQqsqT2Cr6"
    title = "Do you dislike Paperboat? Use this link to opt out."
    html_content += f'<li><a href="{link}">{title}</a></li>'
    
    link = "https://forms.gle/Ecqd264cJKzLUtHQ8"
    title = "Or suggest here a new journal to be added to PaperBoat."
    html_content += f'<li><a href="{link}">{title}</a></li>'
    
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
    message["Subject"] = "Daily PaperBoat Digest - " + receiver_topic
    
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