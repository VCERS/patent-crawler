"""
You should do this steps in order ro run this code:
    * Use Search_Url_Finder.py to Download CSV file which contain url of each patent
    * Copy it (CSV file) to path where this code exist
    * Rename it to gp-search.csv

====Input: Sulfide Solid Electrolyte
Selenium Guide: How To Find Elements by CSS Selectors https://scrapeops.io/selenium-web-scraping-playbook/python-selenium-find-elements-css/
[python libs] https://ualibweb.github.io/UALIB_ScholarlyAPI_Cookbook/src/python/sdirect.html
    
This code extract this information from patents page from Google Patents and store them into datafram:
    - ID
    - Description
    - Publication Date
    - URL
    

This code create two files in the code directory :
    patents_data.csv --> Contain all information scraped from patents pages
    not_scrap_pickle --> Contain all pantents from gp-search.csv which weren't scrapped 



====Libraries used:
[] https://pypi.org/project/markdown2/
[] https://github.com/PaperTurtle/python_html_markdown_converter
[] https://pypi.org/project/markdownify/

@author: LIAO LONGLONG
"""


# Import required packages
import pandas as pd
import progressbar
import time, os, re
from os.path import join
from bs4 import BeautifulSoup
import pickle
from selenium.webdriver.common.by import By
import markdownify, glob
from markdownify import MarkdownConverter   # Convert HTML to markdown, see https://github.com/AI4WA/Docs2KG
import strip_markdown

import json, warnings
import requests
from time import sleep

script_path = os.path.dirname(os.path.abspath(__file__))
warnings.filterwarnings('ignore')

def springer_url_finder(query):
    # specify the base URL of the Springer page to scrape with the "STEM Education" query
    base_url = "https://link.springer.com/search/page/"
    query = '?query=STEM+Education&facet-content-type="Article"&facet-discipline="Education"&facet-sub-discipline="Science+Education"'

    # Initialize an empty list to collect data
    articles_data = []

    # Get the number of pages
    page = 1
    url = base_url + str(page) + query
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    last_page = soup.find("span", class_="number-of-pages")
    if last_page:
        last_page = int(last_page.text)
    else:
        last_page = 1  # If not found, default to 1

    # Loop through all pages
    for page in range(1, last_page + 1):
        print(page, "/", last_page)
        # Construct the URL for the current page
        url = base_url + str(page) + query
        # Make a GET request to the URL
        response = requests.get(url)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the list of articles on the page
        article_list = soup.find("ol", class_="content-item-list")

        # Find all the individual article elements within the list
        if article_list:
            articles = article_list.find_all("li")
            for row in articles:
                titles = row.find_all("h2")
                p_tag = row.find("p", {"class": "content-type"})
                if p_tag is not None and "Article" in p_tag.text:
                    for title in titles:
                        href_value = title.a['href']
                        title_text = title.text.strip()
                        link_complete = "https://link.springer.com" + href_value
                        articles_data.append({"Titles": title_text, "Links": link_complete})
                        print(title_text, " ", link_complete)

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(articles_data)
    # Save to CSV
    df.to_csv('STEM_Education_Articles.csv', index=False)
    print("Data saved to STEM_Education_Articles.csv")
    return df


def get_mate_item(bs, attrs_value='dc.title'):
    # Find the meta tag with name "dc.title"
    meta_tag = bs.find('meta', attrs={'name': attrs_value})
    # Extract the content attribute
    item_content = ""
    if meta_tag and 'content' in meta_tag.attrs:
        item_content = meta_tag['content']        

    return item_content


# Extract the content of the articles published in the journal "Advanced Energy Materials", 'Advanced Materials'
def extract_springAEM_artical(html_file_path="", content_class='main-content', md_path='rstdir'):

    # Read the HTML file
    with open(html_file_path, "r") as file:
        html = file.read()
    # Use Beautidulsoup to extract information from html
    bs = BeautifulSoup(html, 'html.parser')
    print("Extracting data from", html_file_path)

    # paper_title = bs.find(class_=title_class)
    meta_title = bs.find('meta', attrs={'property': 'og:title'})
    paper_title = meta_title['content']
    articles_data = ''
    # paper_title = bs.find('meta', attrs={'name': 'og:title'})['content']
    paper_title = re.sub(r'/', '', paper_title)
    # print(paper_title) 
    # Find the meta tag with name "dc.title"
    # meta_tags = ['dc.title','prism.publicationName','prism.publicationDate','prism.doi']
    # for meta_tag in meta_tags:
    #     articles_data.append({meta_tag: get_mate_item(bs, meta_tag)})
    # print(articles_data)
 
    # Extract description 
    # desc = bs.find(class_=content_class)
    desc_arr = bs.find_all('section', class_=[content_class])
    
    # Remove all <a> tags and their content
    for desc in desc_arr:
        for a in desc.find_all('a'):
            a.decompose()  # This removes the tag and its content      
        # Remove spaces before <i> or after </i> in the HTML content using regular expressions
        desc_str_no_spaces = re.sub(r'\s+(?=<i>)|(?<=</i>)\s+', '', str(desc))
        desc_str_no_spaces = re.sub(r'\s+(?=<sub>)|(?<=</sub>)\s+', '', desc_str_no_spaces)  # remove spaces before <sub> or after </sub>
        desc_str_no_spaces = re.sub(r'\[.*?\]', '', desc_str_no_spaces)  # remove []  

        articles_data = articles_data + '\n' + desc_str_no_spaces

    # Create a new BeautifulSoup object from the modified HTML content
    desc = BeautifulSoup(articles_data, 'html.parser')
    

    # Create shorthand method for conversion
    def md(soup, **options):
        return MarkdownConverter(**options).convert_soup(soup)

    mdfile = join(script_path, md_path, paper_title + ".md")
    with open(mdfile, "w") as file:
        markdown_content = md(desc, strong_em_symbol="", escape_misc=False)  # Convert HTML to markdown
        markdown_content = re.sub(r'\n\s*\n', '\n\n', str(markdown_content))   # Merge consecutive empty lines into a single empty line
        file.write(str(markdown_content))
        # strip_markdown.strip_markdown_file(mdfile, join(script_path, md_path))


def extract_spring_artical(html_file_path, content_class, md_path='rstdir'):

    # Read the HTML file
    with open(html_file_path, "r") as file:
        html = file.read()
    # Use Beautidulsoup to extract information from html
    bs = BeautifulSoup(html, 'html.parser')
    with open("tmp.html", "w") as file:
        file.write(str(bs))

    print("Extracting data from", html_file_path)
    # paper_title = bs.find(class_=title_class)
    meta_title = bs.find('meta', attrs={'property': 'og:title'})
    paper_title = meta_title['content']
    paper_title = re.sub(r'/', '', paper_title) 
    articles_data = ''
    # paper_title = bs.find('meta', attrs={'name': 'og:title'})['content']
    # print(paper_title) 
    # Find the meta tag with name "dc.title"
    # meta_tags = ['dc.title','prism.publicationName','prism.publicationDate','prism.doi']
    # for meta_tag in meta_tags:
    #     articles_data.append({meta_tag: get_mate_item(bs, meta_tag)})
    # print(articles_data)
 
    # Extract description 
    # desc = bs.find(class_=content_class)
    desc_arr = bs.find_all('section', class_=[content_class])
    
    # Remove all <a> tags and their content
    for desc in desc_arr:
        for a in desc.find_all('a'):
            a.decompose()  # This removes the tag and its content      
        # Remove spaces before <i> or after </i> in the HTML content using regular expressions
        desc_str_no_spaces = re.sub(r'\s+(?=<i>)|(?<=</i>)\s+', '', str(desc))
        desc_str_no_spaces = re.sub(r'\s+(?=<sub>)|(?<=</sub>)\s+', '', desc_str_no_spaces)  # remove spaces before <sub> or after </sub>
        desc_str_no_spaces = re.sub(r'\[.*?\]', '', desc_str_no_spaces)  # remove []  

        articles_data = articles_data + '\n' + desc_str_no_spaces

    # Create a new BeautifulSoup object from the modified HTML content
    # desc = BeautifulSoup(desc_str_no_spaces, 'html.parser')
    desc = BeautifulSoup(articles_data, 'html.parser')
    

    # Create shorthand method for conversion
    def md(soup, **options):
        return MarkdownConverter(**options).convert_soup(soup)

    mdfile = join(script_path, md_path, paper_title + ".md")
    with open(mdfile, "w") as file:
        markdown_content = md(desc, strong_em_symbol="", escape_misc=False)  # Convert HTML to markdown
        markdown_content = re.sub(r'\n\s*\n', '\n\n', str(markdown_content))   # Merge consecutive empty lines into a single empty line
        file.write(str(markdown_content))
        # strip_markdown.strip_markdown_file(mdfile, join(script_path, md_path))


if __name__ == "__main__":    

    dir_path = os.path.dirname(os.path.realpath(__file__))
    # htmlfile = "/home/hktai/Downloads/Characterizing Students’ 4C Skills Development During Problem-based Digital Making _ Journal of Science Education and Technology.html"
    
    
    # Directory to search
    jounal_name = 'Advanced Energy Materials'
    jounal_name = 'Advanced Materials'
    jounal_name = 'wiley Small'
    dir_path = join(dir_path, 'sulfideSSE', jounal_name) 

    # Use glob to find all .html files
    # html_files = glob.glob(join(dir_path, '**', '*.html'), recursive=True)
    html_files = glob.glob(join(dir_path, '*.html'), recursive=True)

    content_cls = 'main-content'
    content_cls = 'article-section__content'   # ['Advanced Energy Materials','Advanced Materials']
    # content_cls = 'article__tags__list'

    # Print the paths of all .html files
    for html_file in html_files:
        if os.path.isfile(html_file):
            extract_spring_artical(html_file, content_cls)
