# create_date: 2025-06-06 14:27:55.222215
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# write_date: 2025-07-16 23:59:16.514934
=======
# write_date: 2025-07-23 18:13:04.405740
>>>>>>> Stashed changes
=======
# write_date: 2025-07-21 01:55:20.587697
>>>>>>> Stashed changes
# name: sifen.edi.batch.send
# comment: OK. Genera un edi.event con la información del lote a enviar

import hashlib
from odoo import fields
from lxml import etree
import re
import zipfile
import base64
import datetime
import requests
import json
import xmltodict

sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])
sequence_next = int(sequence.next_by_id())

certificate = self.env['edi.certificate'].search([], limit=1)
documents = []

if record.invoice_ids:
  rows_ids = record.invoice_ids
if record.picking_ids:
  rows_ids = record.picking_ids
  
for invoice in rows_ids:
    vals = {}
    vals['move'] = invoice
    vals['signature_datetime'] = fields.Datetime.context_timestamp(invoice, datetime.datetime.now()).strftime("%Y-%m-%dT%H:%M:%S")
    
    # _logger.info("Document Create Datetime: %s" %(invoice.create_date))
    
<<<<<<< Updated upstream
    invoice_time = datetime.time(hour=invoice.create_date.hour, minute=invoice.create_date.minute, second=invoice.create_date.second )
    invoice_datetime = self.get_local_from_utc(str(invoice.edi_document_datetime))
    _logger.info("***************************************************")
    _logger.info("Documento     : %s" %(invoice.name))
    _logger.info("Fecha Emision : %s" %(invoice_datetime))
    _logger.info("Fecha Firma   : %s" %(vals['signature_datetime']))
    _logger.info("***************************************************")

<<<<<<< Updated upstream
    move_invoice_date = invoice.edi_document_datetime.strftime("%Y-%m-%dT%H:%M:%S")
=======
    # invoice_time = datetime.time(hour=invoice.create_date.hour, minute=invoice.create_date.minute, second=invoice.create_date.second )
    invoice_datetime = self.get_local_from_utc(str(invoice.edi_document_datetime))
    _logger.info("***************************************************")
    _logger.info("Factura: %s" %(invoice.name))
    _logger.info("Fecha Emision: %s" %(invoice_datetime))
    _logger.info("Fecha Firma: %s" %(vals['signature_datetime']))
    _logger.info("***************************************************")

    move_invoice_date = invoice_datetime.strftime("%Y-%m-%dT%H:%M:%S")
>>>>>>> Stashed changes
=======
    move_invoice_date = invoice_datetime.strftime("%Y-%m-%dT%H:%M:%S")
>>>>>>> Stashed changes
    vals['move_invoice_date'] = move_invoice_date

    # _logger.info(vals)

    rde = self.env['edi.template']._render('rDE', **vals)
    try:
      rde_signed = certificate.sign_content(rde, reference_uri=invoice.control_code, id_attribute="Id")
    except BaseException as errstr:
      rde_signed = ""
      _logger.error(errstr)
      for ln, ll in enumerate(rde.split("\n")):
        _logger.info([ln,ll])

    pattern = r'<DigestValue>(.*?)</DigestValue>'
    digest_value = re.findall(pattern, rde_signed)[0]
    digest_value = ''.join([hex(ord(c))[2:] for c in digest_value])

    move_invoice_date_hex = ''.join([hex(ord(c))[2:] for c in move_invoice_date])

    qr_data = "nVersion=%s" % (150)
    qr_data += "&Id=%s" % (invoice.control_code)
    qr_data += "&dFeEmiDE=%s" % (move_invoice_date_hex)
    if invoice.partner_id.l10n_latam_identification_type_id.is_vat:
        if invoice.partner_id.vat:
            if "-" in invoice.partner_id.vat:
                qr_data += "&dRucRec=%s" % (invoice.partner_id.vat.split("-")[0])
            else:
                qr_data += "&dRucRec=%s" %(invoice.partner_id.vat)
        else:
            qr_data += "&dRucRec=0" 
    else:
        if invoice.partner_id.l10n_latam_identification_type_id.edi_code == '5':
            qr_data += "&dNumIDRec=0" 
        else:
            qr_data += "&dNumIDRec=%s" %(invoice.partner_id.vat)
    if record.move_type == 'stock_picking':
        qr_data += "&dTotGralOpe=%.8f" % (0)
        qr_data += "&dTotIVA=%.8f" % (0)
        qr_data += "&cItems=%s" % (len(invoice.move_line_ids_without_package))
    elif record.move_type != 'stock_picking':
        qr_data += "&dTotGralOpe=%.8f" % (invoice.amount_total)
        qr_data += "&dTotIVA=%.8f" % (invoice.amount_tax)
        qr_data += "&cItems=%s" % (len(invoice.invoice_line_ids))
    qr_data += "&DigestValue=%s" % (digest_value)
    qr_data += "&IdCSC=%s" % ("0001")
    qr_data_secret = qr_data + "%s" %(invoice.company_id.security_code_1) 
    qr_hash = hashlib.sha256(qr_data_secret.encode())
    qr_data += "&cHashQR=%s" % (qr_hash.hexdigest())
    qr_data = qr_data.replace("&", "&amp;")
    if self.company_id.sifen_environment == "0":
        qr_link = "https://ekuatia.set.gov.py/consultas-test/qr?%s" % (qr_data)
    else:
        qr_link = "https://ekuatia.set.gov.py/consultas/qr?%s" % (qr_data)

    qr_vals = {}
    qr_vals["qr_link"] = qr_link
    invoice.write({'qr_link':qr_link.replace('&amp;','&')})

    gcamfufd = self.env['edi.template']._render("gCamFuFD", **qr_vals)
    
    # _logger.info("gCamFuFD: %s" %(gcamfufd))

    rde_signed = rde_signed.replace("</rDE>", "%s</rDE>" %(gcamfufd))

    documents.append(rde_signed)
    
    invoice.env['ir.attachment'].create({
                'name': "%s_%s.xml" %(invoice.control_code,datetime.datetime.now().strftime("%Y%m%d_%H%M%S")),
                'datas': base64.b64encode(rde_signed.encode()),
                'type': 'binary',
                'res_model': invoice._name,
                'res_id': invoice.id,
            })
    invoice.send_edi_document()
    

envelope_content = rde_signed
sequence = self.env['ir.sequence'].search([('code', '=', 'SoapEnvelope')])

vals = {}
vals['documents'] = documents
rlotede = self.env['edi.template']._render('rLoteDE', **vals)

base_file_name = f"{sequence_next}"
xml_file_name = f"/mnt/input/{base_file_name}.xml"

xml_file = open(xml_file_name, "wb")
xml_file.write(rlotede.encode())
xml_file.close()

zip_file_name = f"{base_file_name}.zip"
zip_path_name = f"/mnt/input/{base_file_name}.zip"
with zipfile.ZipFile(zip_path_name, "w") as zipf:
    zipf.write(xml_file_name, arcname=f"{base_file_name}.xml")

zipf = open(zip_path_name, "rb")
batch_content = base64.b64encode(zipf.read())
zipf.close()

vals = {}
vals["envelope_sequence"] = sequence_next
vals["batch_content"] = batch_content.decode()

envelope = self.env['edi.template']._render("Envelope_rEnvioLote", **vals)


if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/async/recibe-lote.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/async/recibe-lote.wsdl"
soap_method = '"#%s"' % ("SiRecepLoteDE")

headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

evals = {}
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals['type'] = 'de_batch'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope.encode())
evals["request_filename"] = "%s_batch_envelope.xml" % (sequence_next)

edi_event = self.env['edi.event'].create(evals)
record.in_queue()
