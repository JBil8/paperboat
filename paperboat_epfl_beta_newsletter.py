############ CURRENT CRONTAB SCRIPT IS STORED ON the WS; open with crontab -e
# content: 
#54 21 * * * . /home/fusar/anaconda3/etc/profile.d/conda.sh; conda activate paperboat; ollama serve; ollama pull mistral; /home/fusar/anaconda3/envs/paperboat/bin/python /data/paperbot/paperboat_epfl_beta_newsletter.py  >> /data/paperbot/logfile.log 2>&1




############ ENGINE


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
import pandas as pd
import time
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import gspread
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

#!ollama serve
#!ollama pull mistral # installation instructions here https://docs.llamaindex.ai/en/stable/getting_started/starter_example_local/
#https://github.com/ollama/ollama/blob/main/docs/linux.md
#https://github.com/ollama/ollama/issues/2727

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama

#import keys #############

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
options.add_argument('--headless')
# download the latest chromedriver https://chromedriver.storage.googleapis.com/index.html?path=114.0.5735.90/
# and chrome correspondent version (Luca has it in WS and MAC, copy and install from installer, found online as it is an older, compatible version)
#sudo apt install ./google-chrome-stable_current_amd64.deb
#sudo cp chromedriver /usr/bin/chromedriver
#sudo chown root:root /usr/bin/chromedriver
#sudo chmod +x /usr/bin/chromedriver
#export PATH=$PATH:/usr/local/bin
 
############# TAKE CARE!

#importing links to all journals
links = pd.read_csv("/data/paperbot/paperboat_linksBIO-CHEM-EN-PHOTON.csv")
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
 'Autophagy',"Chemical Society Reviews", "Energy and Environmental Science", "Journal of Materials Chemistry A"]

def duplicate_nature_rows(df):
    mask = df['Journal'].str.contains("Nature")
    duplicates = df[mask].copy()
    duplicates['Link'] = duplicates['Link'] + "?searchType=journalSearch&sort=PubDate&page=2"
    return pd.concat([df, duplicates], ignore_index=True)

# as sometimes there are so many new papers that they end up in multiple pages!
links = duplicate_nature_rows(links)

### for prototyping 
#links = links.iloc[96:,:] ######### 60, 81, 95 CRASH!

#links = links.iloc[[81, 95],:]

#links = links.iloc[19:,:]
print(links)
#print(links)
today = str(datetime.date.today())

pd.DataFrame([today]).to_csv("/data/paperbot/flag.csv")

# Initializing the dataframe to store all data
combined_df = pd.DataFrame(columns=["Title", "Date", "Journal", "Field"])

directory = '/data/paperbot/mist'
filename = "doc.txt"
file_path = os.path.join(directory, filename)

for i in range(0, links.shape[0]):

    print(np.array(links['Journal'])[i])
    
    url = np.array(links['Link'])[i]
    journal = np.array(links['Journal'])[i]
    field = np.array(links['Topic/Field'])[i]
    
    try:
        response = requests.get(url).text 
        soup = BeautifulSoup(response, 'html.parser')
        titles = str(soup.get_text().replace("\n\n", " ")) 
    
    except:
        print("RemoteDisconnected")

    badj = np.array(links['Journal'])[i] in badjournals
    
    print(badj)
    
    condition = (titles == 'Just a moment...Enable JavaScript and cookies to continue') | badj
    
    if condition:
        print("in")
        #options = Options()
        #options.headless = True 
        path_to_chromedriver = '/usr/local/bin/chromedriver'
        service = Service(executable_path=path_to_chromedriver)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5) ######## 0.01
        page_content = driver.page_source
        driver.quit()
        soup = BeautifulSoup(page_content, 'html.parser')
        titles = str(soup.get_text().replace("\n\n", " "))


    

    max_context_length = 4096 ### reasonable heuristic, reduced for mistral

    for k in range(math.ceil(len(titles) / max_context_length)):
        try:
            print(k)
            extracted_titles = []

            start_idx = k * max_context_length
            end_idx = min((k + 1) * max_context_length, len(titles))

            current_titles = titles[start_idx:end_idx]
            
            with open(file_path, 'w') as file:
                file.write(current_titles)

            documents = SimpleDirectoryReader(directory).load_data()
            
            # bge embedding model
            Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
            documents = SimpleDirectoryReader(directory).load_data()
              
            # ollama
            Settings.llm = Ollama(model="mistral", request_timeout=30.0)
            
            index = VectorStoreIndex.from_documents(
                documents,
            )
            
            query_engine = index.as_query_engine()
            response = query_engine.query("Extract paper TITLES from this text. "
                                            "For example, for  'November 2, 2023 |"
                    "https://doi.org/10.1371/journal.pgen.1011021    Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics   "          
                    "              Luke N. Yaeger,              Shawn French,              Eric D. Brown,              Jean Philippe Côté,              Lori L. Burrows        "
                    "PLOS Genetics: published' you will return """"Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"""""
                                           "NEVER return this very same title """"Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"""" or any rephrasing of it. "
                                          "Do not include author names, abbreviations and similar, just titles. If there are no titles but only paragraphs, or empty content, simply return 'NO TITLE' without ANY COMMENT. "
                                          "Do not number the titles, report them just as they are, without modifications. "
                                          "Return one title per line. DO NOT MISS ANY TITLE. We are dealing with scientific "
                                            "paper titles, so return only what's reasonable (e.g., something like "
                                            "'Clinical Trials', 'Developmental Biology', 'Ecology' is likely NOT a title "
                                            "of a paper, it's too generic). Just return the PLAUSIBLE titles, if there are none, just return plain 'NO TITLES', with no further comment, just 'NO TITLES'!. do NOT format "
                                            "with dashes or numbers, just plain titles. remember, it's IMPERATIVE "
                                            "that you change line between subsequent titles!\n\n\n")
                      
            extracted_titles.extend(response.response.split('\n'))

            df = pd.DataFrame(extracted_titles, columns=["Title"])
            df['Date'] = datetime.datetime.today().strftime('%Y-%m-%d')
            df['Journal'] = journal
            df['Field'] = field
            combined_df = pd.concat([combined_df, df], ignore_index=True)

            #print(combined_df)
            
        except Exception as e: 
            current_time = datetime.datetime.now()
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

            with open('log_errors.txt', 'a') as log_file:
                log_file.write(f"{formatted_time} - Error: {str(e)}\n")
            continue

# some hardcoded error control for recurrent errors when using mistral
combined_df = combined_df[combined_df['Title'].apply(lambda x: len(x.split()) > 5)].drop_duplicates()
combined_df = combined_df[~combined_df['Title'].str.contains('title|sub-mic', case=False, regex=True)]

#!pip install requests==2.14.2 #################### (not on the WS, prob. not with llamaindex)

sss = combined_df['Title']

res = []

combined_df.to_csv("todayALLJOURNALS.csv")

for s in tqdm(sss):
    try:
        url = "https://search.yahoo.com/search?p=SUBSTITUTED"
        modified_s = s.replace(" ", "+")
        url = url.replace("SUBSTITUTED", modified_s)
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        
        driver.get(url)
        
        try:
            first_result_link = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "a[data-matarget='algo']"))
            )
            link = first_result_link.get_attribute('href')
        except Exception as e:
            print(str(e))
        #first_result_link = driver.find_element(By.CSS_SELECTOR, "a[data-matarget='algo']")
        #link = first_result_link.get_attribute('href')
        res.append(link)
        driver.quit()
    except Exception as e:
        print("An error occurred:", str(e))
        res.append('Failed')


##### BIORXIV!

from datetime import datetime, timedelta
num = 4
today = datetime.today() - timedelta(days=num) 
today = today.date()

url = "https://www.biorxiv.org/search/jcode%3Abiorxiv%20limit_from%3A"+str(today)+"%20limit_to%3A"+str(today)+"%20numresults%3A1000%20sort%3Arelevance-rank%20format_result%3Astandard"
response = requests.get(url)
titles_and_links = []

if response.status_code == 200:
    html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")

    title_spans = soup.find_all('span', class_='highwire-cite-title')
    
    for span in title_spans:
        title = span.text.strip()  
        
        link_tag = span.find('a')
        if link_tag and 'href' in link_tag.attrs:
            link = link_tag['href']
            if not link.startswith('http'):
                link = f"https://www.biorxiv.org{link}"
            titles_and_links.append((title, link))

df = pd.DataFrame(titles_and_links, columns=['Title', 'Link'])


df['Date'] = datetime.today().strftime('%Y-%m-%d')
df['Journal'] = 'biorXiv, 3 days range - high Twitter engagement'
df['Field'] = 'Bio'
df = df[['Title', 'Date', 'Journal', 'Field', 'Link']]

twitter_mentions_all = []

for LINK in tqdm(df['Link']):
    
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        driver.get(LINK)

        twitter_mentions_element = WebDriverWait(driver, 0.5).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#count_twitter"))
        )

        twitter_mentions = twitter_mentions_element.text
        twitter_mentions_all.append(twitter_mentions)
        driver.quit()
    except:
        twitter_mentions_all.append(0)

df['Tweets'] = [int(i) for i in twitter_mentions_all]
df = df.loc[df['Tweets'] > 30,:]
df = df.iloc[:,:5]

combined_df['Link'] = res
combined_df = pd.concat([combined_df, df], axis=0)

full_df = pd.read_hdf("/data/paperbot/full_df.h5ad", key="table")
full_df = full_df.loc[:, [x!="Unnamed: 0" for x in full_df.columns]]
combined_df = combined_df.loc[~combined_df['Title'].isin(full_df['Title']),:]

combined_df.to_csv("/data/paperbot/today.csv")
full_df = pd.concat([full_df, combined_df], axis=0)
full_df = full_df.drop_duplicates()
full_df.to_hdf("/data/paperbot/full_df.h5ad", key="table")






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
PATH = '/data/paperbot/'

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
#file_contentFULL['Link']="https://chromedriver.storage.googleapis.com/index.html?path=114.0.5735.90/"
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
        
    link = "https://docs.google.com/forms/d/e/1FAIpQLSc4_sTtyDrkao5xQhKtkSSAW3msxJNcRNuWYdTQPdronSo2zA/viewform?usp=sf_link"
    title = "Do you like Paperboat? Use this link to share it with your community!"
    html_content += f'<li><a href="{link}">{title}</a></li>'
 
    link = "https://docs.google.com/forms/d/e/1FAIpQLSc4_sTtyDrkao5xQhKtkSSAW3msxJNcRNuWYdTQPdronSo2zA/viewform?usp=sf_link"
    title = "Do you dislike Paperboat? Use this link to opt out."
    html_content += f'<li><a href="{link}">{title}</a></li>'
    
    link = "https://docs.google.com/forms/d/e/1FAIpQLSe3gRHvV7vmdsmES_96yCxQajbIw_I6c2JuXFDaY8F-q3p7Ow/viewform?usp=sf_link"
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
