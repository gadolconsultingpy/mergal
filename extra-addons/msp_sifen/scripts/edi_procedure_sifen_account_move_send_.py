# create_date: 2025-06-06 14:27:55.222215
# write_date: 2025-06-20 00:33:19.477529
# name: sifen.account.move.send
# comment: DESACTIVADO

import hashlib
from odoo import fields
from lxml import etree
import re
import zipfile
import base64
import datetime
import requests
import xmltodict
import json
from collections import OrderedDict

def clean_xml(de):
  while "  " in de.decode():
    de = de.decode().replace("  "," ").encode()
  while "\n " in de.decode():
    de = de.decode().replace("\n ","\n").encode()
  while "\n\n" in de.decode():
    de = de.decode().replace("\n\n","\n").encode()
  de = de.decode().strip().encode()
  return de

def create_file(invoice, content):
  base_file_name = f"{invoice.control_code}"
  xml_file_name = f"/mnt/input/{base_file_name}_odoo.xml"
  
  file_obj = open(xml_file_name,"w")
  if isinstance(content, bytes):
    file_obj.write(content.decode())
  else:
    file_obj.write(content)
  file_obj.close()