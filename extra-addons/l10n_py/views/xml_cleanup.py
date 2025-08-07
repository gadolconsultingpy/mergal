import os
import xml.etree.ElementTree as ET


def replace_tree_with_list(directory):
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(subdir, file)
                tree = ET.parse(file_path)
                root = tree.getroot()
                modified = False

                for field in root.findall(".//field[@name='name']"):
                    if field.text and field.text.endswith('.tree'):
                        field.text = field.text[:-5] + '.list'
                        modified = True

                if modified:
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)


if __name__ == "__main__":
    directory = '.'
    replace_tree_with_list(directory)