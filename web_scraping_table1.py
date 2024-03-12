#%%
from bs4 import BeautifulSoup as  Soup
import requests as  rq
import pandas as pd
#%%
url="https://en.wikipedia.org/wiki/List_of_largest_companies_in_the_United_States_by_revenue"
page=rq.get(url)
soup = Soup(page.content, 'html.parser')

#%%
print(soup)
#%%
table=soup.find_all("table")[1]
print(table)

#%%
soup.find("table",class_="wikitable sortable")


#%%
#<table class="wikitable sortable jquery-tablesorter">
#<caption>
#%%
world_titles=table.find_all("th")

#%%
world_table_titles=[title.text.strip() for title in world_titles]
print(world_table_titles)
#%%
df=pd.DataFrame(columns=world_table_titles)
df
#%%
column_data=table.find_all("tr")
#%%

for row in column_data[1:]:   #we start from the third row because the first two rows are headers
   row_data= row.find_all("td")
   individual_row_data=[data.text.strip() for data in row_data]
   #print(individual_row_data)

   lenght=len(df)
   df.loc[lenght]=individual_row_data

#%%
#save to csv
filename = "WorldPopulationData.csv"
df.to_csv(filename, index=False)

