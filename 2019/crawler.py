import numpy as np
import pandas as pd 
from pandas import DataFrame
import re
import urllib.request
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

base_url = "https://sofifa.com/players?offset="
columns = ['ID', 'Name', 'Age', 'Photo', 'Nationality', 'Flag', 'Overall', 'Potential', 'Club', 
           'Club Logo', 'Value', 'Wage', 'Special']
data = DataFrame(columns=columns)
for offset in range(304):
    url = base_url + str(offset*60)
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text)
    table_body = soup.find('tbody')
    for row in table_body.findAll('tr'):
        td = row.findAll('td')
        picture = td[0].find('img').get('data-src')
        pid = td[0].find('img').get('id')
        nationality = td[1].find('a').get('title')
        flag_img = td[1].find('img').get('data-src')
        name = td[1].findAll('a')[1].text
        age = td[2].find('div').text.strip()
        overall = td[3].text.strip()
        potential = td[4].text.strip()
        club = td[5].find('a').text
        club_logo = td[5].find('img').get('data-src')
        value = td[6].text.strip()
        wage = td[7].text.strip()
        special = td[8].text.strip()
        player_data = DataFrame([[pid, name, age, picture, nationality, flag_img, overall, potential, club, club_logo, value, wage, special]])
        player_data.columns = columns
        data = data.append(player_data, ignore_index=True)
    offset+=1
data = data.drop_duplicates()
    
master_data = DataFrame()
r = 0
player_data_url = 'https://sofifa.com/player/'
for index, row in data.iterrows():
    skill_names = []
    skill_map = {'ID' : str(row['ID'])}
    url = player_data_url + str(row['ID'])
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text)
    categories = soup.find('div', {'class': 'teams'}).findAll('div', {'class': 'column col-4'})[0:3]
    for category in categories:
        skills = category.findAll('li')
        for skill in skills:
            if(skill.find('label') != None):
                a = skill.text
                n = skill.find('label').text
                value = a.replace(n, '').strip()
                skill_names.append(n)
                skill_map[str(n)] = value
    if(soup.find('aside').find('div', {'class': 'card mb-2'}).find('div', {'class': 'card-body'})):
        card_rows = soup.find('aside').find('div', {'class': 'card mb-2'}).find('div', {'class': 'card-body'}).findAll('div', {'class': 'columns'})
        for c_row in card_rows:
            attributes = c_row.findAll('div', {'class': re.compile('column col-sm-2 text-center')})
            for attribute in attributes:
                if(attribute.find('div')):
                    text = attribute.text
                    name = ''.join(re.findall('[a-zA-Z]', text))
                    value = text.replace(name, '').strip()
                    skill_names.append(name)
                    skill_map[str(name)] = value
    else:
        for name in attr_data.columns[12:38]:
            skill_names.append(name)
            skill_map[str(name)] = None
    sections = soup.find('article').findAll('div', {'class': 'mb-2'})[1:3]
    first = sections[0].findAll('div', {'class': 'column col-4'})
    second = sections[1].findAll('div', {'class': 'column col-4'})[:-1]
    sections = first + second
    for section in sections:
        items = section.find('ul').findAll('li')
        for item in items:
            value = int(re.findall(r'\d+', item.text)[0])
            name = ''.join(re.findall('[a-zA-Z]*', item.text))
            skill_names.append(name)
            skill_map[str(name)] = value
    attr_data = DataFrame(columns=skill_names)
    for key in skill_map.keys():
        if(key == 'Position'):
            if(skill_map['Position'] in ('RES', 'SUB')):
                skill_map['Position'] = soup.find('article').find('div', {'class': 'meta'}).find('span').text
        attr_data.loc[r,key] = skill_map[key]
    r = r + 1
    attr_data = attr_data.loc[:, ~attr_data.columns.duplicated()]
    master_data = master_data.append([attr_data])
 
full_data = pd.merge(data, master_data, left_index=True, right_index=True)
full_data.drop('ID_y', axis=1, inplace=True)
full_data = full_data.rename(index=str, columns={"ID_x": "ID"})
full_data.to_csv('data.csv', encoding='utf-8-sig')
