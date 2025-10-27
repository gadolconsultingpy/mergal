# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.account.move.consult
# comment: OK. Crea un edi.event que procesa la consulta del CDC

import requests
import xmltodict
import re
import json
import base64
from lxml import etree

# record = account.move
sequence = self.env['ir.sequence'].search([('code', '=', 'rEnviConsDeRequest')])

vals = {}
vals['consult_sequence'] = int(sequence.next_by_id())
vals['cdc'] = record.control_code

if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/consultas/consulta.wsdl"
soap_method = '"#SiConsDE"'

headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

envelope = self.env['edi.template']._render("Envelope_rEnviConsDeRequest", **vals)

evals = {}
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'de_consult'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope.encode())
evals["request_filename"] = "%s.xml" %(record.control_code)

edi_event = self.env['edi.event'].create(evals)
