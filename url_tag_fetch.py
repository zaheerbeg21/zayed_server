import xml.etree.ElementTree as ET
import urllib.request

import json


import requests

r = requests.get('https://www.zu.ac.ae/main/en/all_pages_json.json')
print(r.json())
# Using a JSON string
with open('json_data.json', 'w') as json_:
    json_.write(r.json())

# def fetch_tag(xml_url):
#     f = urllib.request.urlopen(xml_url)
#     url_data = f.read().decode('utf-8')
#     xmlTree = ET.parse(url_data)
#
#     elemList = []
#     for elem in xmlTree.iter():
#         elemList.append(elem.tag)
#
#     elemList = list(set(elemList))
#     print(elemList)
#
#     return elemList
#
#
# lst = fetch_tag('https://www.zu.ac.ae/main/en/all_news.xml')
# print(lst)

###to write xml usng url
# import requests
#
# URL = "https://www.zu.ac.ae/main/en/all_news.xml"
#
# data = requests.get(URL)
# with open('feed.xml', 'wb') as xmlfile:
#     xmlfile.write(data.content)

#### working using file
# def fetch_tag(xml_file):
#     xmlTree = ET.parse(xml_file)
#
#     elemList = []
#
#     for elem in xmlTree.iter():
#         elemList.append(elem.tag)
#
#     elemList = list(set(elemList))
#     print(elemList)
#
#     return elemList
#
#
# fetch_tag('F:\\Live_from_Server\\July_07_2022\\zu_chatbot_server_\\all_pages_ar.xml')



