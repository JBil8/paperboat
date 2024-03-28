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
import keys


sss = np.array(["Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"])

res = []

for s in sss:
    url = "https://www.bing.com/search?q=SUBSTITUTED"
    modified_s = s.replace(" ", "+")
    url = url.replace("SUBSTITUTED", modified_s)
    response = requests.get(url).text 
    soup = BeautifulSoup(response, 'html.parser')
    titles = str(soup.get_text().replace("\n\n", " ")) ##### for the limit on gpt4
    
    url_pattern = r'https?:\/\/(?:www\.)?[^\s]{2,}'
    
    urls = re.findall(url_pattern, titles)
    
    first_url = urls[0]
    
    if "..." in first_url or "…" in first_url:
        first_url = urls[1]
        for i in range(len(first_url), 0, -1): 
            if first_url[:i] and s.startswith(first_url[i-1:]):
                first_url = first_url[:i-1]
                break
        res.append(first_url)
    else:
        for i in range(len(first_url), 0, -1): 
            if first_url[:i] and s.startswith(first_url[i-1:]):
                first_url = first_url[:i-1]
                break
        res.append(first_url)
    print(first_url)

