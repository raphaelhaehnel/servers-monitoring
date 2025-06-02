import xml.etree.ElementTree as ET

def get_config():
    # Load from file
    tree = ET.parse('config.xml')
    return tree.getroot()