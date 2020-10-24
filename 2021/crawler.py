from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

# Get basic players information for all players
base_url = "https://sofifa.com/players?offset="
columns = ['ID', 'Name', 'Age', 'Photo', 'Nationality', 'Flag', 'Overall', 'Potential', 'Club', 'Club Logo', 'Value', 'Wage', 'Special']
data = pd.DataFrame(columns = columns)


for offset in range(0, 335):
    url = base_url + str(offset * 60)
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    table_body = soup.find('tbody')
    for row in table_body.findAll('tr'):
        td = row.findAll('td')
        picture = td[0].find('img').get('data-src')
        pid = td[0].find('img').get('id')
        nationality = td[1].find('img').get('title')
        flag_img = td[1].find('img').get('data-src')
        name = td[1].find("a").get("data-tooltip")
        age = td[2].text
        overall = td[3].text.strip()
        potential = td[4].text.strip()
        club = td[5].find('a').text
        club_logo = td[5].find('img').get('data-src')
        value = td[6].text.strip()
        wage = td[7].text.strip()
        special = td[8].text.strip()
        player_data = pd.DataFrame([[pid, name, age, picture, nationality, flag_img, overall, potential, club, club_logo, value, wage, special]])
        player_data.columns = columns
        data = data.append(player_data, ignore_index=True)
    print("done for "+str(offset),end="\r")
data = data.drop_duplicates()
data.head()

# Get detailed player information from player page
detailed_columns = ['Preferred Foot','Weak Foot','Skill Moves','International Reputation','Work Rate','Body Type','Real Face','Release Clause','Position','Jersey Number','Joined','Contract Valid Until','Height','Weight','LS','ST','RS','LW','LF','CF','RF','RW','LAM','CAM','RAM','LM','LCM','CM','RCM','RM','LWB','LDM','CDM','RDM','RWB','LB','LCB','CB','RCB','RB','GK','Likes','Dislikes','Following','Crossing','Finishing','Heading Accuracy','Short Passing','Volleys','Dribbling','Curve','FK Accuracy','Long Passing','Ball Control','Acceleration','Sprint Speed','Agility','Reactions','Balance','Shot Power','Jumping','Stamina','Strength','Long Shots','Aggression','Interceptions','Positioning','Vision','Penalties','Composure','Defensive Awareness','Standing Tackle','Sliding Tackle','GK Diving','GK Handling','GK Kicking','GK Positioning','GK Reflexes']
detailed_data = pd.DataFrame(index = range(0, data.count()[0]), columns = detailed_columns)
detailed_data["ID"] = data["ID"].values

player_data_url = 'https://sofifa.com/player/'
count = 0
for id in data["ID"][:20]:
    url = player_data_url + str(id)
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'html.parser')
    skill_map = {}
    columns = soup.find("div", {"class":"columns"})
    columns12 = columns.find_all("div",{"class":"column col-12"})
    for column in columns12:
        skills = column.findAll('li')
        for skill in skills:
            if(skill.find('label') != None):
                label = skill.find('label').text
                value = skill.text.replace(label, '').strip()
                skill_map[label] = value
    meta_data = soup.find('div', {'class': 'meta'}).text.split(' ')
    length = len(meta_data)
    weight = meta_data[length - 1]
    height = meta_data[length - 2].split('\'')[0] + '\'' + meta_data[length - 2].split('\'')[1].split('\"')[0]
    skill_map["Height"] = height
    skill_map['Weight'] = weight
    if('Position' in skill_map.keys()):
        if skill_map['Position'] in ('', 'RES', 'SUB'):
            skill_map['Position'] = soup.find('div', {'class': 'meta bp3-text-overflow-ellipsis'}).find('span').text
        if(skill_map['Position'] != 'GK'):
            card_rows = soup.find("div",{"class":"lineup"}).find_all("div",{"class":"column col-sm-2"})
            for attribute in card_rows:
                if(attribute.find('div')):
                    name = ''.join(re.findall('[a-zA-Z]', attribute.text))
                    value = attribute.text.replace(name, '').strip()
                    skill_map[str(name)] = value
    skill_map["Likes"] = columns12[3].find("button",{"class":"bp3-button like-btn need-sign-in"}).find("span",{"class":"count"}).text
    skill_map["Dislikes"] = columns12[3].find("button",{"class":"bp3-button dislike-btn need-sign-in"}).find("span",{"class":"count"}).text
    skill_map["Following"] = columns12[3].find("button",{"rel":"nofollow"}).find("span",{"class":"count"}).text
    name = []
    value = []
    columns3 = columns.find_all("ul",{"class":"pl"})
    switch = 0
    for column in columns3[3:]:
        for li in column.find_all("li"):
            text = li.text
            name.append(text[2:].strip(" ").rstrip())
            value.append(text[:2].strip(" ").rstrip())
    for name, value in zip(name[:-2],value[:-2]):
        skill_map[name] = value
    count = count + 1
    print("Loaded so far: "+str(count)+"/"+str(data.shape[0]), end="\r")
    for key, value in skill_map.items():
        detailed_data.loc[detailed_data["ID"] == id, key] = value

full_data = pd.merge(data, detailed_data.iloc[:,:79], how = 'inner', on = 'ID')
full_data.to_csv('data.csv', encoding='utf-8-sig')
