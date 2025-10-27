# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.account.move.invalid
# comment: OK. Crea un edi.event para invalidar documentos

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

certificate = self.env['edi.certificate'].search([], limit=1)

signature_datetime = fields.Datetime.context_timestamp(record, fields.Datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")
sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])
event_sequence = self.env['ir.sequence'].search([('code', '=', 'edi.event')])
event_sequence = event_sequence.next_by_id()
event_id = int(event_sequence)

vals = {}
vals['event_id'] = event_id
vals['record'] = record
vals['signature_datetime'] = signature_datetime

rgeseveinvalid = self.env['edi.template']._render("rGesEve_invalid",**vals)
rgeseveinvalid_signed = certificate.sign_content(rgeseveinvalid, reference_uri=str(event_id), id_attribute="Id")

vals = {}
vals["envelope_sequence"] = int(sequence.next_by_id())
vals["event_content"] = rgeseveinvalid_signed
envelope_renvieventode = self.env['edi.template']._render("Envelope_rEnviEventoDe",**vals)

if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/eventos/evento.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/eventos/evento.wsdl"

soap_method = '"#SiRecepEvento"'
headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

record.write({'state':'sent'})

evals = {}
evals['name'] = event_sequence
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'de_invalid'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope_renvieventode.encode())
evals["request_filename"] = "%s.xml" %(record.name)

edi_event = self.env['edi.event'].create(evals)
