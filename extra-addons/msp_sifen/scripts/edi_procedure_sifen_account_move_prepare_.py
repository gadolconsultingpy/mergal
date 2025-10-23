# create_date: 2025-06-06 14:27:55.222215
# write_date: 2025-07-16 23:59:00.429926
# name: sifen.account.move.prepare
# comment: OK. Crea un edi.event y preparando el contenido del DE

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

vals = {}
vals['move'] = record
vals['signature_datetime'] = fields.Datetime.context_timestamp(record, datetime.datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")

invoice_time = datetime.time(hour=record.create_date.hour, minute=record.create_date.minute, second=record.create_date.second )
invoice_datetime = datetime.datetime.combine(record.invoice_date, invoice_time)
invoice_datetime = fields.Datetime.context_timestamp(record, invoice_datetime)
invoice_datetime = self.get_local_from_utc(str(record.edi_document_datetime))

move_invoice_date = invoice_datetime.strftime("%Y-%m-%dT%H:%M:%S")
vals['move_invoice_date'] = move_invoice_date

rde = self.env['edi.template']._render('rDE', **vals)

rde_signed = certificate.sign_content(rde, reference_uri=record.control_code, id_attribute="Id")

pattern = r'<DigestValue>(.*?)</DigestValue>'
digest_value = re.findall(pattern, rde_signed)[0]
digest_value = ''.join([hex(ord(c))[2:] for c in digest_value])

print("move_invoice_date", move_invoice_date)
move_invoice_date_hex = ''.join([hex(ord(c))[2:] for c in move_invoice_date])
print("move_invoice_date_hex", move_invoice_date_hex)

qr_data = "nVersion=%s" %(150)
qr_data += "&Id=%s" %(record.control_code)
qr_data += "&dFeEmiDE=%s" %(move_invoice_date_hex)
if record.partner_id.l10n_latam_identification_type_id.is_vat :
  qr_data += "&dRucRec=%s" %(record.partner_id.vat.split("-")[0])
else:
  if record.partner_id.l10n_latam_identification_type_id.edi_code == '5':
    qr_data += "&dNumIDRec=0" 
  else:
    qr_data += "&dNumIDRec=%s" %(record.partner_id.vat)
qr_data += "&dTotGralOpe=%.8f" %(record.amount_total)
qr_data += "&dTotIVA=%.8f" %(record.amount_tax)
qr_data += "&cItems=%s" %(len(record.invoice_line_ids))
qr_data += "&DigestValue=%s" %(digest_value)
qr_data += "&IdCSC=%s" %("0001")
qr_data_secret = qr_data + "%s" %(record.company_id.security_code_1) 
qr_hash = hashlib.sha256(qr_data_secret.encode())
qr_data += "&cHashQR=%s" %(qr_hash.hexdigest()) 
qr_data = qr_data.replace("&","&amp;")
if self.company_id.sifen_environment == "0":
  qr_link = "https://ekuatia.set.gov.py/consultas-test/qr?%s" %(qr_data)
else:
  qr_link = "https://ekuatia.set.gov.py/consultas/qr?%s" %(qr_data)

vals["qr_link"] = qr_link
record.write({'qr_link':qr_link.replace('&amp;','&')})

gcamfufd = self.env['edi.template']._render("gCamFuFD", **vals)

rde_signed = rde_signed.replace("</rDE>", "%s</rDE>" %(gcamfufd))

envelope_content = rde_signed
sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])
vals = {}
vals["envelope_sequence"] = int(sequence.next_by_id())
vals["envelope_content"] = envelope_content
# vals["xml_version"] = '<?xml version="1.0" encoding="UTF-8"?>'

if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/sync/recibe.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/sync/recibe.wsdl"
soap_method = '"#%s"' %("SiRecepDE")

envelope = self.env['edi.template']._render("Envelope_rEnviDe", **vals)

headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

log_data = {}
log_data["method"] = soap_method
log_data["path"] = url
log_data["request"] = envelope
log_data["type"] = 'outbound'
log_data["tag"] = self.name
log_data["record"] = record
# try:
# if True:
cert_path = self.env['edi.certificate'].prepare_cert_file(record.company_id.id)
# cert_path = "/mnt/input/F1T_15401.pem" 

evals = {}
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'de'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
# evals["request"] = envelope
evals["request_content"] = base64.b64encode(envelope.encode())
evals["request_filename"] = "%s.xml" %(record.control_code)

edi_event = self.env['edi.event'].create(evals)
record.write({'sifen_state':'queue'})