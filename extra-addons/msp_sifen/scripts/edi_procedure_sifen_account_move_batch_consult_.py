# create_date: 2024-12-20 13:06:15.256760
# write_date: 2024-12-20 13:06:54.563885
# name: sifen.account.move.batch.consult
# comment: OK. Consulta Lotes de Documentos

import requests
import xmltodict
from lxml import etree

sequence = self.env['ir.sequence'].search([('code', '=', 'rEnviConsLoteDe')])

# print("record", record._name)
if record._name == 'sefal.procedure':
  batch_control = self.env['lote.control'].search([("lote_num_sifen",">",0)],order="fecha, id")
else:
  batch_control = record

# print("batch_control", batch_control)
for bc in batch_control:
  vals = {}
  vals['batch_consult_sequence'] = int(sequence.next_by_id())
  vals['batch_number'] = bc.lote_num_sifen_char
  
  rEnviConsLoteDe = self.env['ir.qweb']._render("l10n_py_edi_templates.rEnviConsLoteDe", vals)
  
  if self.company_id.sifen_environment == "0":
    url = "https://sifen-test.set.gov.py/de/ws/consultas/consulta-lote.wsdl"
  else:
    url = "https://sifen.set.gov.py/de/ws/consultas/consulta-lote.wsdl"
  headers = {}
  headers['Content-Type'] = "application/soap+xml"
  headers['SOAPAction'] = '"#%s"' %("SiConsLoteDE")
  
  response = requests.post(url=url, headers=headers, data=rEnviConsLoteDe, cert="/mnt/input/F1T_15401.pem")
  
  xmltree = xmltodict.parse(response.content)
  
  rProtDe = dict(xmltree.get("env:Envelope",{}).get("env:Body",{}).get("ns2:rResEnviConsLoteDe",{}))