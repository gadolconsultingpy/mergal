# create_date: 2025-05-07 02:29:56.284065
# write_date: 2025-05-20 10:33:59.052103
# name: sifen.account.move.cancel
# comment: ARCHIVAR. Crea un edi.event para enviar una cancelación de documento a la SIFEN.

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
if record.edi_document_type_code == '7':
  vals['record'] = record.picking_id
elif record.edi_document_type_code in ['1','5']:
  vals['record'] = record.invoice_id
vals['signature_datetime'] = signature_datetime
vals['cancel_reason'] = record.reason

rgesevecancel = self.env['edi.template']._render("rGesEve_cancel",**vals)
rgesevecancel_signed = certificate.sign_content(rgesevecancel, reference_uri=str(event_id), id_attribute="Id")

vals = {}
vals["envelope_sequence"] = int(sequence.next_by_id())
vals["event_content"] = rgesevecancel_signed
envelope_renvieventode = self.env['edi.template']._render("Envelope_rEnviEventoDe",**vals)

if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/eventos/evento.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/eventos/evento.wsdl"

soap_method = '"#SiRecepEvento"'
headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

evals = {}
evals['name'] = event_sequence
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'de_cancel'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope_renvieventode.encode())
if record.edi_document_type_code == '7':
  evals["request_filename"] = "%s.xml" %(record.picking_id.control_code)
elif record.edi_document_type_code in ['1','5']:
  evals["request_filename"] = "%s.xml" %(record.invoice_id.control_code)


edi_event = self.env['edi.event'].create(evals)
