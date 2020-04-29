import clearbit
import json
import os
import pandas as pd
import configparser
import requests
import nltk

api_url_base = 'https://company.clearbit.com/v1/'
source_file = 'credit-inst.csv'
out_file = 'domainresolution.csv'
colname = "Firm"

if os.getenv('CLEARBIT_TOKEN'):
    clearbit.key = os.getenv('CLEARBIT_TOKEN')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    clearbit.key = config['clearbit']['key']

headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer {0}'.format(clearbit.key)}

df = pd.read_csv(source_file)
df = df[:35]

def nouns(name):
    tokens = nltk.word_tokenize(name)
    stopwords = ['Ltd.', 'Co.', '(UK)', 'UK', 'Limited', 'Assurance', 'Society', 'Ltd', 'plc', 'Co', 
                 'Financial', 'Company', 'Branch', 'Group', 'London', 'Corporation', 'PLC', 'FS', 'Plc']
    tokens = [word for word in tokens if word not in stopwords]
    tags = nltk.pos_tag(tokens)
    # print(tags)
    nouns = [word for word,pos in tags if (pos == 'NNP' or pos == 'JJ' or pos == 'NN')]
    nouns = ' '.join(nouns)
    # name = [[' '.join(i)] for i in nouns]
    return nouns

def get_domain(name):
    # based on https://clearbit.com/docs?shell#name-to-domain-api

    api_url = '{}domains/find?name={}'.format(api_url_base, name)
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return None


for index, row in df.iterrows():
    # TODO: only process Authorised firms
    print("processing {}".format(row[colname]))
    nounname = str(nouns(row[colname]))
    print("nouns are: {}".format(nounname))

    # lets first try full name and if that doesn't resolve
    # then we try the nouns in the name
    name = get_domain(row[colname])
    if name is None:
        # try with nounname
        name = get_domain(nounname)
        if name is None:
            df.loc[index,'domain'] = "none"
            df.loc[index,'nounname'] = nounname
        else:
            df.loc[index,'domain'] = name['domain']
            df.loc[index,'nounname'] = nounname
            print("found: {}".format(name['domain']))

    else:
        df.loc[index,'domain'] = name['domain']
        df.loc[index,'nounname'] = nounname
        print("found: {}".format(name['domain']))
        # record = df.loc[index, :]
        # record = pd.DataFrame(record)
        # record = record.transpose()
        # record.to_csv('list.csv', mode='a', header=False)
        # del record

df.to_csv(out_file)