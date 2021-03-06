#!/usr/bin/env python3
import requests
import json
import pandas as pd 
from pandas.io.json import json_normalize
import os
import configparser

source = 'domainresolution-all-banks-clean-no-dupes.csv'
out_file = 'mailhunter.csv'
domains = 'domain'

df = pd.read_csv(source)
# df = df[:5]

if os.getenv('snov_client_id'):
    client_id = os.getenv('snov_client_id')
    client_secret = os.getenv('snov_client_secret')
else:
    config = configparser.ConfigParser()
    config.read('secrets')
    client_id = config['snov']['client_id']
    client_secret = config['snov']['client_secret']


def get_access_token():
    global client_id, client_secret
    params = {
        'grant_type':'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    res = requests.post('https://api.snov.io/v1/oauth/access_token', data=params)
    resText = res.text.encode('ascii','ignore')
    return json.loads(resText)['access_token']


def get_domain_search(domain):
    token = get_access_token()
    params = {'access_token':token,
            'domain':domain,
            'type': 'personal',
            'offset': 0,
            'limit': 100
    }
    res = requests.post('https://api.snov.io/v1/get-domain-emails-with-info', data=params)
    return json.loads(res.text)


normalised = pd.DataFrame()

# drop duplicate domains to not use API call twice on same domain
df = df.drop_duplicates(subset=['domain'])

for index, row in df.iterrows():
    domain = row[domains]
    if domain != 'none' and domain != 'nan.' and domain != 'wikipedia.org' and domain != '4icu.org':
        print("processing {} {}".format(index, domain))
        try:
            emails = get_domain_search(domain)
        except Exception as e:
            print(e)

        try:
            emdf = json_normalize(emails['emails'])
            emdf['org'] = emails['companyName']

            if 'twitter' not in emdf.columns:
                emdf['twitter'] = 'nan.' 

            # fail safe csv writing just in case we get interrupted:
            emdf = emdf[sorted(emdf)]
            emdf.to_csv('list.csv', mode='a', header=False, encoding='utf-8')
            normalised = normalised.append(emdf, sort=True)

        except Exception as e:
            print(e)

normalised.to_csv(out_file, encoding='utf-8')
