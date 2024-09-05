"""
You should do this steps in order ro run this code:
    * Use Search_Url_Finder.py to Download CSV file which contain url of each patent
    * Copy it (CSV file) to path where this code exist
    * Rename it to gp-search.csv

====Input: Sulfide Solid Electrolyte
Selenium Guide: How To Find Elements by CSS Selectors https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-find-elements-css/

Patent ID [4]: https://patents.google.com/patent/US11355780B2/en, 
    
This code extract this information from patents page from Google Patents and store them into datafram:
    - ID
    - Description
    - Publication Date
    - URL
    
The code have capability to resume from last run. So don't worry if something unwanted happend (i.e  Power outage!)

This code create two files in the code directory :
    patents_data.csv --> Contain all information scraped from patents pages
    not_scrap_pickle --> Contain all pantents from gp-search.csv which weren't scrapped 
    
@author: zil.ink/anvaari
"""


# Import required packages
import pandas as pd
import requests
import progressbar
import time, os, re
from os.path import join
from bs4 import BeautifulSoup
import pickle
from selenium.webdriver.common.by import By
from markdownify import MarkdownConverter   # Convert HTML to markdown, see https://github.com/AI4WA/Docs2KG
import strip_markdown


script_path = os.path.dirname(os.path.abspath(__file__))

# Make sure gp-search.csv exist  
while not os.path.isfile(join(script_path, 'gp-search.csv')):
    print(
        '\nYou should do this steps in order ro run this code:\n\t* Use Search_Url_Finder.py to Download CSV file which contain url of each patent\n\t* Copy it (CSV file) to path where this code exist\n\t* Rename it to gp-search.csv\n')
    print("\ngp-search.csv doesn't find. It should exist where this code exist\n")
    temp_ = input('\nPlease copy the file and  press Enter\n')
# Import search-gp.csv as dataframe
search_df = pd.read_csv(join(script_path, 'gp-search.csv'), skiprows=[0])


# Load list of not scraped links if exist
if os.path.isfile(join(script_path, 'not_scrap_pickle')):
    with open(join(script_path, 'not_scrap_pickle'), 'rb') as fp:
        not_scraped = pickle.load(fp)
else:
    not_scraped = []

# Set user agent for every request send to google    
h = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'}

# Iteate over search-gp.csv and send request to server
for (index, row), i in zip(search_df.iterrows(), progressbar.progressbar(range(len(search_df)))):
    link = row['result link']
    # Send request to Google Patents and scrap source of patent page
    # try except use in order handle connection errors
    try:
        r = requests.get(link, headers=h)
    except requests.exceptions.ConnectionError as e:
        not_scraped.append(link)
        print(e, '\n\n')
        # This piece closes the program if rate of errors go higher than 20% 
        if len(not_scraped) / int(index) >= 0.2:
            print('\nAbove half of request result in erroe please read the output to investigate why this happend\n')
            break
        continue
    # Use Beautidulsoup to extract information from html
    bs = BeautifulSoup(r.content, 'html.parser')

    # Extract description
    desc = bs.find('section', {'itemprop': 'description'})
    
    # Remove spaces before <i> or after </i> in the HTML content using regular expressions
    desc_str_no_spaces = re.sub(r'\s+(?=<i>)|(?<=</i>)\s+', '', str(desc))
    desc_str_no_spaces = re.sub(r'\s+(?=<sub>)|(?<=</sub>)\s+', '', desc_str_no_spaces)
    
    # desc_str = str(desc)
    # desc_str_no_spaces = desc_str.replace(' <i>', '<i>')

    # Create a new BeautifulSoup object from the modified HTML content
    desc = BeautifulSoup(desc_str_no_spaces, 'html.parser')
    with open("output.html", "w") as file:
        file.write(str(desc))

    # Create shorthand method for conversion
    def md(soup, **options):
        return MarkdownConverter(**options).convert_soup(soup)

    mdfile = join(script_path, "rstdir", row['id']+".md")
    with open(mdfile, "w", encoding='utf-8') as file:
        # file.write(md(desc, strong_em_symbol="", sub_symbol="~", sup_symbol="^"))
        markdown_content = md(desc, strong_em_symbol="", escape_misc=False)  # Convert HTML to markdown
        markdown_content = re.sub(r'\n\s*\n', '\n\n', str(markdown_content))   # Merge consecutive empty lines into a single empty line
        file.write(str(markdown_content))
        strip_markdown.strip_markdown_file(mdfile, join(script_path, "rstdir"))
        file.close()

    # Handle situation where description not exist
    if not desc is None:
        # Handle situation where description have non-english paragraphs
        if desc.find('span', class_='notranslate') is None:
            desc = desc.text.strip()
        else:
            notranslate = [tag.find(class_='google-src-text') for tag in desc.find_all('span', class_='notranslate')]
            for tag in notranslate:
                tag.extract()
            desc = desc.text.strip()
    else:
        desc = 'Not Found'

