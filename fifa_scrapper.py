import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import numpy as np

def vers_available(value = None,id = None):
    if value == 'latest':
        url = 'https://sofifa.com/players'
        source_code = requests.get(url)
        plain_text = source_code.text
        soup = BeautifulSoup(plain_text, 'lxml')
        latest_vers = ''.join(re.findall('[0-9]*',soup.body.find('div',class_='bp3-menu').find('a',href=True)['href']))
        return latest_vers
    else:
        next_v = '190074'
        player_data_url = 'https://sofifa.com/player/'+str(id)+'/'+next_v
        url_vers = requests.get(player_data_url).url.split('/')[-1]
        return url_vers == next_v
vers_available(id=251854)
def vers_convertion():
    vers_text = soup.find_all('span',class_='bp3-button-text')[1].text.split(' ')
    vers_text.pop(1)
    return ''.join(vers_text)
def money_convertion(value):
    if value[-1] == 'M':
        return eval(value[:-1])*1000000
    elif value[-1] == 'K':
        return eval(value[:-1])*1000

versions = [vers_available('latest'),'190074']
base_url = "https://sofifa.com/players?offset="
columns = ['ID', 'Name', 'Age', 'Nationality','value']
data = pd.DataFrame(columns = columns)
for offset in range(0, 100):
    url = base_url + str(offset * 61)
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'lxml')
    table_body = soup.find('tbody')
    for row in table_body.findAll('tr'):
        try:
            td = row.findAll('td')
            pid = td[0].find('img').get('id')
            nationality = td[1].find('img').get('title')
            name = td[1].find('a').text.strip()
            age = eval(td[2].text.strip())
            value = money_convertion(td[6].text[1:])
            if td[1].find('a',href=True)['href'].split('/')[-2] == vers_available('latest') and vers_available(id=pid):
                player_data = pd.DataFrame([[pid, name, age, nationality,value]])
                player_data.columns = columns
                data = data.append(player_data, ignore_index=True)
        except:
            pass
data = data.drop_duplicates()
data.fillna(np.nan,inplace=True)
data = data[(data.Age < 26) & (pd.notna(data.value))][['ID', 'Name', 'Age', 'Nationality']]
# Get detailed player information from player page
player_data_url = 'https://sofifa.com/player/'
all_player_detailed = pd.DataFrame(columns=[])
for id in data.ID:
    detailed_data = {'ID':id}
    for vers in versions:
        url = player_data_url + id + '/' + vers
        source_code = requests.get(url)
        if source_code.url.split('/')[-1] == vers:
            plain_text = source_code.text
            soup = BeautifulSoup(plain_text, 'lxml')
            physical_data = soup.body.find('div',class_='meta bp3-text-overflow-ellipsis').text
            profile_values = soup.find('div',class_='bp3-card double-spacing').findAll('li')
            dicotomic_func = lambda x: 1 if x == 'Right' or x == 'Yes' else 0
            detailed_data_ver = {
            'overall' : eval(soup.body.find('section').find('div',class_='column col-3').find('span').text),
            'potential' : eval(soup.body.find('section').findAll('div',class_='column col-3')[1].find('span').text),
            'player_value' : money_convertion(soup.body.find('section').findAll('div',class_='column col-3')[2].text.split('Value')[0][1:]),
            'player_wage' : money_convertion(soup.body.find('section').findAll('div',class_='column col-3')[3].text.split('Wage')[0][1:]),
            'height' : ((eval(physical_data.split(') ')[1].split(' ')[0].split("\'")[0])*12) + eval(physical_data.split(') ')[1].split(' ')[0].split("\'")[1].split('"')[0])) * 2.54,
            'weight' : eval(physical_data.split(') ')[1].split(' ')[1][:3]),
            'preferred_foot' : dicotomic_func(profile_values[0].text.split('Preferred Foot')[1]),
            'weak_foot' : eval(profile_values[1].text[0]),
            'skill_moves' : eval(profile_values[2].text[0]),
            'international_reputation' : eval(profile_values[3].text[0]),
            'work_rate' : profile_values[4].span.text,
            'real_face' : dicotomic_func(profile_values[6].span.text),
            'Club' : soup.find_all('h5')[2].text,
            'Loaned' : 1 if soup.body.find('ul',class_='bp3-text-overflow-ellipsis pl text-right').find_all('li')[-2].label.text == 'Loaned From' else 0,
            'best_position' : soup.body.find_all('div',class_='flex-centered')[4].find_all('li',class_='bp3-text-overflow-ellipsis')[-2].span.text,
            'best_overall_rating' : eval(soup.body.find_all('div',class_='flex-centered')[4].find_all('li',class_='bp3-text-overflow-ellipsis')[-1].span.text)
            }
            # >>Map data<<
            field_stats = soup.body.find('div',class_='field-small').find_all('div',class_='columns-sm half-spacing')
            statsXline_dict = {}
            statnum = 1
            for lines in field_stats:
                line = lines.find_all('div',class_='column col-sm-2')
                val_list = []
                statsXline_dict['MapAvgLine'+str(statnum)] = val_list
                statnum += 1
                for vals in line:
                    try:
                        val_list.append(eval(str(vals.contents[0]).split('<br/>')[1].split('</div>')[0]))            
                    except:
                        pass
                statsXline_dict = {k : np.mean(v) for k,v in statsXline_dict.items()}
            detailed_data_ver.update(statsXline_dict)
            # >>Attributes<<
            if len(soup.body.find('div',class_='column col-12').find_all('div',class_='column col-3')) == 16:
                detailed_attributes = soup.body.find('div',class_='column col-12').find_all('div',class_='column col-3')[8:15]
            else:
                detailed_attributes = soup.body.find('div',class_='column col-12').find_all('div',class_='column col-3')[7:14]
            attributes_dict = {}
            for attribute_column in detailed_attributes:
                line = attribute_column.find_all('li')
                for vals in line:
                    tag = ''.join(re.findall('[a-zA-Z]*',vals.text))
                    stat_value = eval(vals.span.text)
                    attributes_dict[tag] = stat_value
            detailed_data_ver.update(attributes_dict)
            detailed_data_ver = {k+'_'+vers_convertion():v for k, v in detailed_data_ver.items()}
            detailed_data.update(detailed_data_ver)
    detailed_dataDF = pd.DataFrame([detailed_data])
    all_player_detailed = all_player_detailed.append(detailed_dataDF,True)
data = data.merge(all_player_detailed,on='ID')
data.drop('value',axis=1,inplace=True)
data.fillna(np.nan,inplace=True)
data.to_csv('./fifa-scouting-data.csv')