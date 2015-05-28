try:
  from lxml import etree as ET
except ImportError:
  try:
    import xml.etree.cElementTree as ET
  except ImportError:
    try:
      import xml.etree.ElementTree as ET
    except ImportError:
      try:
        import cElementTree as ET
      except ImportError:
        try:
          import elementtree.ElementTree as ET
        except ImportError:
          print("Failed to import ElementTree from any known place")
from collections import defaultdict
import pprint
import re
import codecs
import json


"""
Count tags and attributes in file. Check for any problematic char in attribute 'k'.
"""
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    if element.tag == "tag":
        addr = element.attrib['k']
        if lower.match(addr):
            keys['lower'] += 1
        elif lower_colon.match(addr):
            keys['lower_colon'] += 1
        elif problemchars.search(addr):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
    return keys

def count_tags(filename):
        tag_count = {}
        attrib_count = {}
        k_count = {}
        keys ={'lower':0, 'lower_colon':0, 'problemchars':0, 'other':0}
        for event, elem in ET.iterparse(filename):
            keys = key_type(elem, keys)
            if elem.tag in tag_count.keys():
                tag_count[elem.tag] += 1
            else:
                tag_count[elem.tag] = 1
            if elem.get('k'):
                if elem.get('k') in k_count.keys():
                    k_count[elem.get('k')] += 1
                else:
                    k_count[elem.get('k')] = 1
            for attr in elem.attrib.keys():
                if attr in attrib_count.keys():
                    attrib_count[attr] += 1
                else:
                    attrib_count[attr] = 1
            elem.clear()
        print 'tag_count: '
        pprint.pprint(sorted(tag_count.iteritems(), key=lambda d:d[1], reverse = True))
        print 'attrib_count: '
        pprint.pprint(sorted(attrib_count.iteritems(), key=lambda d:d[1], reverse = True))
        print 'k_value_count: '
        pprint.pprint(sorted(k_count.iteritems(), key=lambda d:d[1], reverse = True))
        print 'problematic chars? '
        pprint.pprint(keys)
        return

# count_tags('sample.osm')
# count_tags('houston_texas.osm')

def check_v_value(filename, tags):
    """
    Return a dictionary containing tags as keys and the sets of all possible values in the file as values.
    """
    k_values = {}
    for tag in tags:
        k_values[tag] = set()
    for event, elem in ET.iterparse(filename, events=('end',)):
        if elem.get('k') in tag_names:
            if elem.get('k') in tags:
                k_values[elem.get('k')].add(elem.get('v'))
        elem.clear()
    return k_values

# tag_names = [k_value_count[i][0] for i in range(20)]
# print tag_names
# tag_names = ['tiger:county', 'tiger:reviewed', 'tiger:source', 'tiger:separated', 'tiger:name_type', 'tiger:zip_left', 'tiger:zip_right', 'power', 'oneway', 'service', 'building', 'surface', 'amenity', 'addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode', 'addr:state', 'gnis:county_name', 'tiger:zip_right_1', 'tiger:zip_left_1']

# pprint.pprint(check_v_value('sample.osm', tag_names))
# pprint.pprint(check_v_value('houston_texas.osm', tag_names))
# pprint.pprint(check_v_value('cleaned_file.osm', tag_names))

"""
Transform xml to JSON. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB.

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to
update the street names before you save them to JSON.

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings.
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons"]
mapping_general = { "St": "Street",
            "St.": "Street",
            "street": "Street",
            'Rd': 'Road',
            'Rd.': 'Road',
            'Ave': 'Avenue',
            'Ave.': 'Avenue',
            'AVE': 'Avenue',
            'AVENUE': 'Avenue',
            'Fwy': 'Freeway',
            'Frwy': 'Freeway',
            'Hwy': 'Highway',
            'Pkwy': 'Parkway',
            'Pky': 'Parkway',
            'Pwky': 'Parkway',
            'Dr.': 'Drive',
            'Dr': 'Drive',
            'Blvd.': 'Boulevard',
            'Blvd': 'Boulevard',
            'blvd.': 'Boulevard',
            'blvd': 'Boulevard',
            'ct': 'Court',
            'Ln': 'Lane',
            'W': 'West',
            'W.': 'West',
            'N': 'North',
            'N.': 'North',
            'S': 'South',
            'S.': 'South',
            'E': 'East',
            'E.': 'East'}
mapping_special = {'Maroneal': 'Maroneal Street',
            'Durham': 'Durham Drive',
            'Bailey': 'Bailey Road',
            'Oaks': 'Oaks Block',
            'Fuzzel': 'Fuzzel Road',
            'Westheimer': 'Westheimer Road',
            'Beechnut': 'Beechnut Street',
            'Driscoll': 'Driscoll Street',
            'Caroline': 'Caroline Street',
            'Hillcroft': 'Hillcroft Street', #or Avenue, both point to the same location
            'Bertner': 'Bertner Avenue',
            'Felipe': 'Felipe Street',
            'Rock': 'Rock Road',
            'Westhimer': 'Westheimer Road',
            'Welford': 'Welford Drive',
            'Hidalgo': 'Hidalgo Street',
            'Blossom': 'Blossom Street',
            'Richmond': 'Richmond Avenue',
            'Kempwood': 'Kempwood Drive',
            'Graustark': 'Graustark Street',
            'Valley': 'Valley Drive', #or Court is correct too
            'Knolls': 'Knolls Drive',
            'Montrose': 'Montrose Boulevard'
            }

def update_street_name_special(name, mapping):
    name_type = name.split(' ')[-1]
    try:
        return name.replace(name_type, mapping[name_type])
    except:
        # print 'Type not found in mapping: ', name
        return name

def update_street_name_general(name, mapping):
    name = name.strip()
    words = name.split(' ')
    for i, word in enumerate(words):
        if word[0].islower():
            word = word[0].upper() + word[1:]
            words[i] = word
    return ' '.join([mapping.get(w, w) for w in words])

def clean_element(element):
      if element.tag in ('node', 'way', 'relation'):
            for tag in element.iter('tag'):
                  #Handle problematic 'addr:city' and add "addr:state" if necessary
                  if tag.get('k') == 'addr:city':
                        if tag.get('v') != tag.get('v').split(',')[0]:
                              tag.attrib['v'] = tag.get('v').split(',')[0]
                              ET.SubElement(element, "tag", {"k":"addr:state","v":"TX"})
                  elif tag.get('k') == 'addr:housenumber':
                        tag.attrib['v'] = tag.get('v').replace('-A', ' #A')
                        tag.attrib['v'] = tag.get('v').replace('-B', ' #B')
                        tag.attrib['v'] = tag.get('v').replace(' A', ' #A')
                  elif tag.get('k') == 'addr:postcode':
                        tag.attrib['v'] = tag.get('v').replace('TX ', '')
                  elif tag.get('k') == 'addr:state':
                        tag.attrib['v'] = 'TX'
                  elif tag.get('k') == 'service':
                        if tag.attrib['v'] == 'drive-through':
                              tag.attrib['v'] = 'drive_through'
                  elif tag.get('k') == 'tiger:county':
                        tag.attrib['v'] = tag.attrib['v'].replace('; ', ':')
                        tag.attrib['v'] = tag.attrib['v'].replace(';', ':')
                  elif tag.get('k') == 'addr:street':
                        st = tag.attrib['v']
                        st = update_street_name_general(st, mapping_general)
                        tag.attrib['v'] = st
                        if st.split(' ')[-1] not in expected:
                              tag.attrib['v'] = update_street_name_special(st, mapping_special)
      return element

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    node = {}
    if element.tag in ("node", "way"):
        node['type'] = element.tag
        for attr in element.attrib.keys():
            if attr in CREATED:
                if 'created' in node.keys():
                    node['created'][attr] = element.attrib[attr]
                else:
                    node['created'] = {attr: element.attrib[attr]}
            elif attr in ['lon', 'lat']:
                pass
            else:
                node[attr] = element.attrib[attr]
            try:
                node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
            except:
                pass
        for nd in element.iter('nd'):
            if 'node_refs' in node.keys():
                node['node_refs'].append(nd.attrib['ref'])
            else:
                node['node_refs'] = [nd.attrib['ref']]
        for t in element.iter('tag'):
            tag_name = t.attrib['k']
            if tag_name == 'type':
                tag_name = 'k_type'
            if problemchars.search(tag_name):
                pass
            elif tag_name[:5] == 'addr:':
                if tag_name.count(':') > 1:
                    pass
                else:
                    key = tag_name.split(":")[-1]
                    if 'address' in node.keys():
                        node['address'][key] = t.attrib['v']
                    else:
                        node['address'] = {key: t.attrib['v']}
            else:
                  node[tag_name] = t.attrib['v']
        return node
    else:
        return None


def process_map(file_in, file_out, pretty = False):
    # file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in, tag=('node', 'way')):
            element = clean_element(element)
            el = shape_element(element)
            if el:
                # data.append(el)
                if pretty:
                  fo.write(json.dumps(el, indent=2)+"\n")
                else:
                  fo.write(json.dumps(el) + "\n")
            element.clear()
    # return data
    return

# process_map('sample.osm', 'sample.json')
# process_map('houston_texas_manually_cleaned.osm', 'cleaned.json')

def write_cleaned_file(input_file, output_file):
    with open(output_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        for i, element in ET.iterparse(input_file, tag=('node', 'way', 'relation')):
            element = clean_element(element)
            output.write(ET.tostring(element, encoding='utf-8'))
            element.clear()
        output.write('</osm>')

write_cleaned_file('houston_texas_manually_cleaned.osm', 'cleaned_file.osm')
