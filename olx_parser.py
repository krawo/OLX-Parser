#Import bibliotek
import pandas as pd
from bs4 import BeautifulSoup
import requests
import seaborn as sns
from datetime import datetime, timedelta
sns.set_style("whitegrid")

#Dni miesiąca do zamiany stringów "dzisiaj" i "wczoraj"
today = str(datetime.today().day)
yesterday = str((datetime.today()-timedelta(1)).day)



#Funkcja do apply - dodanie 0 przed jednocyfrowymi dniami
def daty_naprawa(row):
    if len(row) == 5:
        return "0" + str(row)
    else:
        return row
    
    
#Funkcja do zliczania liczby stron w ramach wyszukiwanego przedmiotu
def count_pages(url):
    request = requests.get(url).text
    soup = BeautifulSoup(request, 'html.parser')
    pages = []
    last_page = soup.find_all("a", {"class":"block br3 brc8 large tdnone lheight24"})
    for x in last_page:
        pages.append(x.get_text(strip=True))
    return int(pages[-1])

#Parser dla jednej strony wyszukiwanego przedmiotu
def olx_page_parser(url):
    request = requests.get(url).text
    soup = BeautifulSoup(request, 'html.parser')
    #Tytuły ogłoszeń
    titles_list = []
    h3 = soup.find_all("h3", {"class":"lheight22 margintop5"})
    for x in h3:
        titles_list.append(x.find('a').get_text(strip=True))
    
    #Ceny
    prices_list = []
    prices = soup.find_all("p", {"class":"price"})
    for x in prices:
        prices_list.append(x.get_text(strip=True))
    
    #Lokalizacje
    locations_list = []
    locations = soup.find_all("small", {"class" : "breadcrumb x-normal"})
    i = 0
    for x in locations:
        try:
            if i % 2 == 0:
                locations_list.append(x.find('span').get_text(strip=True))
            i+=1
        except AttributeError:
            pass
        
    #Daty dodania ogłoszeń
    dates_list = []
    dates = soup.find_all("small", {"class" : "breadcrumb x-normal"})
    i = 1
    for x in dates:
        if i % 3 == 0:
            dates_list.append(x.get_text(strip=True))
        i+=1
        
    #Stworzenie DataFrame z list
    df = pd.DataFrame({'Tytul' : titles_list,
                      'Cena': prices_list,
                      'Lokalizacja': locations_list,
                      'Data dodania' : dates_list})
    return df

#Crawler po stronach i processing dat
def parse_olx(url, filename):
    pages = count_pages(url)
    df = pd.DataFrame()
    #Pętla - wykonaj scraping dla każdej strony wyszukiwanego przedmiotu
    for page in range (1, pages):
        print("Scrapuję stronę " + str(page))
        new_url = url + "?page=" + str(page)
        df_page = olx_page_parser(new_url)
        df = df.append(df_page)
    df = df.drop_duplicates()
    #Naprawienie dat
    df["Data dodania"] = df["Data dodania"].apply(daty_naprawa)
    df["Data dodania"] = df["Data dodania"].replace({"dzisiaj" : today+" lut", "wczoraj" : yesterday+" lut"}, regex=True)
    df["Data dodania"] = df["Data dodania"].apply(lambda x: x.split()[0:2])
    df["Data dodania"] = df["Data dodania"].apply(lambda x: ' '.join(x))
    df["Data dodania"] = df["Data dodania"].replace({"sty" : "/01", "lut" : "/02"}, regex=True)
    df["Data dodania"] = '2020/' + df["Data dodania"]
    df["Data dodania"] =  df["Data dodania"].replace({" ": ""}, regex=True)
    df["Data dodania"] = pd.to_datetime(df["Data dodania"], format='%Y/%d/%m')
    df = df.sort_values(by='Data dodania')
    df = df.set_index(["Data dodania"])    
    #Zamiana ceny na wartość liczbową
    df["Cena"] = df["Cena"].replace({" zł" : "", "Zamienię" : np.nan, " " : "", "," : "."}, regex=True)
    df["Cena"] = df["Cena"].astype(float)
    #Zapisanie do pliku xlsx
    df.to_excel(filename+".xlsx")
    return df