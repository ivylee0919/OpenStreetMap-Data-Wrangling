#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re



lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
lower_colon_2 = re.compile(r'^([a-z]|_)*:([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
FILENAME = '../dataset/sample.osm'


def key_type(element, keys):
    if element.tag == "tag":
        if re.match(lower, element.attrib["k"]):
            keys["lower"] += 1
        elif re.match(lower_colon, element.attrib["k"]):
            keys["lower_colon"] += 1
        elif re.match(lower_colon_2, element.attrib["k"]):
            keys["lower_colon_2"] += 1
        elif re.search(problemchars, element.attrib["k"]):
            keys["problemchars"] += 1
        else:
            keys["other"] += 1
            # print element.attrib["k"]
        
    return keys

def count_keys(filename):
    keys_count={}

    for _,elem in ET.iterparse(filename):
        if elem.tag == "tag":
            if elem.attrib["k"] not in keys_count:
                keys_count[elem.attrib["k"]] = 1
            else:
                keys_count[elem.attrib["k"]] += 1

    return sorted(keys_count.items(), key=lambda x:x[1], reverse = True)

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0,"lower_colon_2":0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys


if __name__ == "__main__":
    
    keys = process_map(FILENAME)
    keys_count = count_keys(FILENAME)

    # pprint.pprint(keys)
    pprint.pprint(keys_count)