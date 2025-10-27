# create_date: 2024-12-20 13:06:15.256760
# write_date: 2024-12-20 13:06:32.846100
# name: sifen.res.partner.vat.consult
# comment: OK. Consulta Datos del Contribuyente

import requests
import json
import base64
from lxml import etree

# SiConsRUC

sequence = self.env['ir.sequence'].search([('code', '=', 'SiConsRUC')])

vals = {}
vals["sequence_id"] = int(sequence.next_by_id())
vals["vat"] = "80013853"
if "-" in record.vat:
  vals["vat"] = record.vat.split("-")[0]
else:
  vals["vat"] = record.vat

if self.company_id.sifen_environment == '0':
  url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta-ruc.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/consultas/consulta-ruc.wsdl"

soap_method = '"#%s"' %("SiConsRUC")

envelope_renviconsruc = self.env['edi.template']._render("Envelope_rEnviConsRUC",**vals)

headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

evals = {}
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'vat_consult'
evals["company_id"] = record.company_id.id if record.company_id else self.env.company.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope_renviconsruc.encode())
evals["request_filename"] = "%s.xml" %(record.name)

edi_event = self.env['edi.event'].create(evals)
