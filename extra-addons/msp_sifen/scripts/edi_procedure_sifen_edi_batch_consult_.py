# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.edi.batch.consult
# comment: OK. Crea un edi.event para consultar el estado de Procedimiento de un Lote.

import json
import base64
from lxml import etree

#record = edi.batch

sequence = self.env['ir.sequence'].search([('code', '=', 'rEnviConsLoteDe')])

if self.company_id.sifen_environment == "0":
  url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta-lote.wsdl"
else:
  url = "https://sifen.set.gov.py/de/ws/consultas/consulta-lote.wsdl"
soap_method = '"#SiResultLoteDE"'
headers = {}
headers['Content-Type'] = "application/soap+xml"
headers['SOAPAction'] = soap_method

vals = {}
vals['batch_consult_sequence'] = int(sequence.next_by_id())
vals['batch_number'] = record.sifen_batch_nr

envelope = self.env['edi.template']._render("Envelope_rEnviConsLoteDe", **vals)

evals = {}
evals['url'] = url
evals['method'] = "POST"
evals['headers'] = json.dumps(headers, indent=4)
evals['soap_method'] = soap_method
evals["type"] = 'de_batch_consult'
evals["company_id"] = record.company_id.id
evals["procedure_id"] = self.id
evals["res_model"] = record._name
evals["res_id"] = record.id
evals["res_name"] = record.name
evals["request_content"] = base64.b64encode(envelope.encode())
evals["request_filename"] = "Lote%s.xml" %(record.name)

edi_event = self.env['edi.event'].create(evals)
record.in_queue()