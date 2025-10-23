import hashlib
from odoo import fields
from lxml import etree
import re
import zipfile
import base64
import requests
import xmltodict

# invoice = self.env['account.move'].browse(83729)
invoice = record

vals = {}
vals['move'] = invoice
move_invoice_date = fields.Datetime.context_timestamp(invoice, invoice.create_date).strftime("%Y-%m-%dT%H:%M:%S")
vals['move_invoice_date'] = move_invoice_date

de_template = "l10n_py_edi_templates.de"
de = self.env['ir.qweb']._render(de_template, vals)
# while "  " in de.decode():
  # de = de.decode().replace("  "," ").encode()
# while "\n " in de.decode():
  # de = de.decode().replace("\n ","\n").encode()
# while "\n\n" in de.decode():
  # de = de.decode().replace("\n\n","\n").encode()

# print("SDE", [sde])
# print("SDE", sde)

certificate = self.env['edi.certificate'].search([], limit=1)
data_signed_str = certificate.sign_content(de.decode())
# print(data_signed_str)

pattern = r'<DigestValue>(.*?)</DigestValue>'
digest_value = re.findall(pattern, data_signed_str)[0]
# print(digest_value)
digest_value = ''.join([hex(ord(c))[2:] for c in digest_value])
# print("digest_value",digest_value)


move_invoice_date_hex = ''.join([hex(ord(c))[2:] for c in move_invoice_date])

qr_data = "nVersion=%s" %(150)
qr_data += "&Id=%s" %(invoice.control_code)
qr_data += "&dFeEmiDE=%s" %(move_invoice_date_hex)
qr_data += "&dNumIDRec=%s" %(invoice.partner_id.vat.split("-")[0])
qr_data += "&dTotGralOpe=%.8f" %(invoice.amount_total)
qr_data += "&dTotIVA=%.8f" %(invoice.amount_tax)
qr_data += "&cItems=%s" %(len(invoice.invoice_line_ids))
qr_data += "&DigestValue=%s" %(digest_value)
qr_data += "&IdCSC=%s" %("1")
qr_data += "%s" %("ABCD0000000000000000000000000000")
qr_hash = hashlib.sha256(qr_data.encode())
qr_data += "&cHashQR=%s" %(qr_hash.hexdigest())
qr_link = "https://ekuatia.set.gov.py/consultas/qr?%s" %(qr_data)

vals["document_de"] = data_signed_str
vals["qr_link"] = qr_link

rde_template = "l10n_py_edi_templates.rde"
rde = self.env['ir.qweb']._render(rde_template, vals)

vals["rde_document"] = rde
rlote_de_template = "l10n_py_edi_templates.rlotede"
rlote_de = self.env['ir.qweb']._render(rlote_de_template, vals)

sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])
sequence_next = int(sequence.next_by_id())

xml_file = open(f"/mnt/input/Lote{sequence_next}.xml","wb")
xml_file.write(rlote_de)
xml_file.close()

base_file_name = f"Lote{sequence_next}"
xml_file_name = f"/mnt/input/{base_file_name}.xml"
zip_file_name = f"/mnt/input/{base_file_name}.zip"
with zipfile.ZipFile(zip_file_name, "w") as zipf:
  zipf.write(xml_file_name, arcname=f"{base_file_name}.xml")

zipf = open(zip_file_name,"rb")
envelope_content = base64.b64encode(zipf.read())
zipf.close()

vals = {}
vals["envelope_sequence"] = sequence_next
vals["envelope_content"] = envelope_content

envelope_template = "l10n_py_edi_templates.envelope"
envelope = self.env['ir.qweb']._render(envelope_template, vals)

# print("ENVELOPE", envelope.decode())

url = "https://sifen-test.set.gov.py/de/ws/async/recibe-lote.wsdl"
headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = '"#%s"' %("SiRecepLoteDE")

response = requests.post(url=url, headers=headers, data=envelope, cert="/mnt/input/F1T_15401.pem")

xmltree = xmltodict.parse(response.content)

rProtDe = xmltree.get("env:Envelope",{}).get("env:Body",{}).get("ns2:rResEnviLoteDe",{})

dFecProc = rProtDe.get("ns2:dFecProc")
dCodRes =  rProtDe.get("ns2:dCodRes")
dMsgRes = rProtDe.get("ns2:dMsgRes")

print("="*30)
print("dFecProc", dFecProc)
print("dCodRes", dCodRes)
print("dMsgRes", dMsgRes)



log_data = {}
log_data["method"] = "SiRecepLoteDE"
log_data["path"] = url
log_data["request"] = envelope
log_data["type"] = 'outbound'
log_data["tag"] = 'account.move.batch.send'
log_data["record"] = invoice
log_data["response"] = etree.tostring(etree.fromstring(response.content), pretty_print=True)
self.env['service.log'].register(**log_data)
