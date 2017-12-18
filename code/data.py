#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

# import cerberus

# import schema
from collections import defaultdict

OSM_PATH = "../dataset/hong-kong.osm"

NODES_PATH = "../dataset/nodes.csv"
NODE_TAGS_PATH = "../dataset/nodes_tags.csv"
WAYS_PATH = "../dataset/ways.csv"
WAY_NODES_PATH = "../dataset/ways_nodes.csv"
WAY_TAGS_PATH = "../dataset/ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def multi_cuisine_apart(tag_dict):
    """
    将有多个菜系的 cuisine，用 ; 分开，整理为一个列表
    如果只有一个菜系，则为一个元素的列表
    最终返回这个菜系列表 cuisine_list
    """
    cuisine_list=[]
    if ";" in tag_dict['value']:
        cuisine_list = tag_dict['value'].split(';')
        # print cuisine_list
    else:
        cuisine_list.append(tag_dict['value'])
    return cuisine_list

def find_zh_en_name(elem):
    """
    name:zh 和 name:en 将被分别储存在 zh 和 en 中并最终组合为 zh_en_name 返回
    同时返回值还有 has_name 用来解决有 name:zh 和 name:en 却没有 name key 时的情况
    """
    zh = ""
    en = ""
    zh_en_name=""
    has_name = False
    for child in elem:
        if child.tag == "tag":

            if (child.attrib['k'] == "name:zh") or (child.attrib['k'] == "name:zh-yue"):
                # 中文要处理 zh-yue 的情况
                zh = child.attrib['v']
            if child.attrib['k'] == "name:en":
                en = child.attrib['v']
            if child.attrib['k'] == "name":
                has_name = True
    if zh and en:
        zh_en_name = zh + " " + en   
    return zh_en_name, has_name



def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}

    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    node_id = element.attrib["id"]
    nd_pos = 0

    zh_en_name, has_name = find_zh_en_name(element) # 调用函数查看是否有 name，zh 和 en
    if (zh_en_name) and (not has_name):
        tag_dict_name={}                        # 如果没有 name，但是有 zh 和 en，则创建一个新的 name 条目
        tag_dict_name["id"] = node_id
        tag_dict_name["key"] = "name"
        tag_dict_name["value"] = zh_en_name
        tag_dict_name["type"] = default_tag_type
        tags.append(tag_dict_name)

    # YOUR CODE HERE
    for child in element:
        
        tag_dict = {}
        way_node = {}      
        if child.tag == "tag":           
            k_data = child.attrib['k']
            colon = re.search(LOWER_COLON, k_data)
            prob = re.search(PROBLEMCHARS, k_data)         
            if prob:
                continue
            else:
                tag_dict["id"] = node_id
                tag_dict["value"] = child.attrib["v"]
                if colon:
                    tag_dict['key'] = k_data.split(':', 1)[1]
                    tag_dict['type'] = k_data.split(':', 1)[0]
                else:
                    tag_dict["key"] = k_data
                    tag_dict["type"] = default_tag_type
                
                
                if (tag_dict['key'] == 'name') and zh_en_name:    # 如果 key 为 name，并且 zh 和 en 都不为空
                    tag_dict["value"] = zh_en_name                # 则修改 name 对应的 value
                
                if tag_dict['key'] == 'cuisine':                   # 处理 key 为 cuisine 的数据
                    cuisine_list = multi_cuisine_apart(tag_dict)
                    for cuisine in cuisine_list:
                        tag_dict_cuisine = tag_dict.copy()
                        tag_dict_cuisine["value"] = cuisine
                        tags.append(tag_dict_cuisine)
                else:
                    tags.append(tag_dict)
                    
        elif child.tag == "nd":
            way_node["id"] = node_id
            way_node["node_id"] = child.attrib["ref"]
            way_node["position"] = nd_pos
            nd_pos += 1
            way_nodes.append(way_node)

    if element.tag == 'node':
        for node_field in node_attr_fields:
            node_attribs[node_field] = element.attrib[node_field]
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for way_field in way_attr_fields:
            way_attribs[way_field] = element.attrib[way_field]
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# def validate_element(element, validator, schema=SCHEMA):
#     """Raise ValidationError if element does not match schema"""
#     if validator.validate(element, schema) is not True:
#         field, errors = next(validator.errors.iteritems())
#         message_string = "\nElement of type '{0}' has the following errors:\n{1}"
#         error_string = pprint.pformat(errors)
        
#         raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        # validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
