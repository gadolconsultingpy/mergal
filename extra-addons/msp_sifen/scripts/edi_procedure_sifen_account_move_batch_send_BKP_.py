# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-02 01:19:51.830800
# name: sifen.account.move.batch.send.BKP
# comment: 

import hashlib
from odoo import fields
from lxml import etree
import re
import zipfile
import base64
import datetime
import requests
import xmltodict


def clean_xml(de):
    while "  " in de.decode():
        de = de.decode().replace("  ", " ").encode()
    while "\n " in de.decode():
        de = de.decode().replace("\n ", "\n").encode()
    while "\n\n" in de.decode():
        de = de.decode().replace("\n\n", "\n").encode()
    de = de.decode().strip().encode()
    return de


def create_file(invoice, content):
    base_file_name = f"{invoice.control_code}"
    xml_file_name = f"/mnt/input/{base_file_name}_odoo_batch.xml"

    file_obj = open(xml_file_name, "w")
    if isinstance(content, bytes):
        file_obj.write(content.decode())
    else:
        file_obj.write(content)
    file_obj.close()


try:
    invoice = record
except:
    pass
# invoice = self.env['account.move'].browse(83801)
certificate = self.env['edi.certificate'].search([], limit=1)

vals = {}
vals['move'] = invoice
vals['signature_datetime'] = fields.Datetime.context_timestamp(invoice, datetime.datetime.now()).strftime(
    "%Y-%m-%dT%H:%M:%S")
move_invoice_date = fields.Datetime.context_timestamp(invoice, invoice.create_date).strftime("%Y-%m-%dT%H:%M:%S")
vals['move_invoice_date'] = move_invoice_date

de = self.env['ir.qweb']._render("l10n_py_edi_templates.de", vals)

vals["de_document"] = de
rde = self.env['ir.qweb']._render("l10n_py_edi_templates.rde", vals)

data_signed_str = certificate.sign_content(rde.decode(), reference_uri=invoice.control_code, id_attribute="Id")

pattern = r'<DigestValue>(.*?)</DigestValue>'
digest_value = re.findall(pattern, data_signed_str)[0]
digest_value = ''.join([hex(ord(c))[2:] for c in digest_value])

move_invoice_date_hex = ''.join([hex(ord(c))[2:] for c in move_invoice_date])

qr_data = "nVersion=%s" % (150)
qr_data += "&Id=%s" % (invoice.control_code)
qr_data += "&dFeEmiDE=%s" % (move_invoice_date_hex)
qr_data += "&dRucRec=%s" % (invoice.partner_id.vat.split("-")[0])
qr_data += "&dTotGralOpe=%.8f" % (invoice.amount_total)
qr_data += "&dTotIVA=%.8f" % (invoice.amount_tax)
qr_data += "&cItems=%s" % (len(invoice.invoice_line_ids))
qr_data += "&DigestValue=%s" % (digest_value)
qr_data += "&IdCSC=%s" % ("001")
qr_data_secret = qr_data + "%s" %(invoice.company_id.security_code_1) 
qr_hash = hashlib.sha256(qr_data_secret.encode())
qr_data += "&cHashQR=%s" % (qr_hash.hexdigest())
qr_data = qr_data.replace("&", "&amp;")
if self.company_id.sifen_environment == '0':
  qr_link = "https://ekuatia.set.gov.py/consultas-test/qr?%s" % (qr_data)
else:
  qr_link = "https://ekuatia.set.gov.py/consultas/qr?%s" % (qr_data)

vals["qr_link"] = qr_link

gcamfufd = self.env['ir.qweb']._render("l10n_py_edi_templates.gcamfufd", vals)

data_signed_str = data_signed_str.replace("</rDE>", "%s</rDE>" % (gcamfufd.decode()))

vals = {}
vals['rde_document'] = data_signed_str.strip()
data_signed_str = self.env['ir.qweb']._render("l10n_py_edi_templates.rlotede", vals)
data_signed_str = data_signed_str.strip()

create_file(invoice, data_signed_str)

sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])
sequence_next = int(sequence.next_by_id())

base_file_name = f"{sequence_next}_1"
xml_file_name = f"/mnt/input/{base_file_name}.xml"

xml_file = open(xml_file_name, "wb")
xml_file.write(data_signed_str)
xml_file.close()

zip_file_name = f"/mnt/input/{base_file_name}.zip"
with zipfile.ZipFile(zip_file_name, "w") as zipf:
    zipf.write(xml_file_name, arcname=f"{base_file_name}.xml")

zipf = open(zip_file_name, "rb")
envelope_content = base64.b64encode(zipf.read())
zipf.close()

vals = {}
vals["envelope_sequence"] = sequence_next
vals["envelope_content"] = envelope_content
vals["xml_version"] = '<?xml version="1.0" encoding="UTF-8"?>'


envelope = self.env['ir.qweb']._render("l10n_py_edi_templates.renviolote_envelope", vals)
envelope = envelope.decode().replace("<env:Header></env:Header>", "<env:Header/>").strip().encode()

if self.company_id.sifen_environment == '0':
  url = "https://sifen-test.set.gov.py/de/ws/async/recibe-lote.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/async/recibe-lote.wsdl"
soap_method = '"#%s"' % ("SiRecepLoteDE")

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


try:
  response = requests.post(url=url, headers=headers, data=envelope, cert="/mnt/input/F1T_15401.pem")

  try:
    xmltree = xmltodict.parse(response.content)
    log_response = etree.tostring(etree.fromstring(response.content), pretty_print=True)
  except BaseException as errstr:
    log_response = response.content.decode()

  log_data["response"] = log_response 
  log_data["status_code"] = response.status_code
  log_data["reason"] = response.reason
  log_record = self.env['service.log'].register(**log_data)

except BaseException as errstr:
  log_data["response"] = errstr
  log_data["status_code"] = "999"
  log_data["reason"] = "BaseException"
  log_record = self.env['service.log'].register(**log_data)

