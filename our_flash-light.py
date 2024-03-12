#%% libraries
import requests 
from bs4 import BeautifulSoup as soup
import pandas as pd
#%% functions
def get_page(url):
    page = requests.get(url)
    return soup(page.content, 'html.parser')
    
def find_all(array, target):
    return [i for i in array if target in i]

#%% Adım 1: URL'yi oluştur ve web sayfasına eriş
URL = "https://www.sec.gov/Archives/edgar/data/"
page = get_page(URL)
entries = page.find_all('a', class_='dir-entry2')
company_list = [entry['href'] for entry in entries]

#%% Adım 2: HTML'i ayrıştırarak belirli bilgileri bul
def parse_company_list(companies):
    company_dicts = []
    for company in companies:
        try:
            company_name = company.split('/')[3].strip()
            cik_number = company.split('/')[5][:-6]
            link = URL + company
            company_info = {'CIK': cik_number, 'Name': company_name, 'Link': link}
            company_dicts.append(company_info)
        except IndexError:
            continue
    return company_dicts

company_info = parse_company_list(company_list)
df = pd.DataFrame(company_info)
print(df)

#%% Adım 3: Veriyi kaydet
df.to_csv('company_info.csv', index=False)
