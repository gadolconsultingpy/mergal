# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.edi.event.de_consult
# comment: OK. Envia a la SIFEN la consulta de CDC

# record = edi.event
import requests
import json
import base64
import re
from lxml import etree
import html

# print("Record in edi.event: %s" %(record._name))

headers = json.loads(record.headers)
cert_path = self.env['edi.certificate'].prepare_cert_file(company_id=record.company_id.id, recreate=True)

invoice = self.env[record.res_model].search([('id', '=', record.res_id)])

request_content = base64.b64decode(record.request_content)

log_data = {}
log_data["method"] = record.soap_method
log_data["path"] = record.url
log_data["request"] = request_content.decode()
log_data["type"] = 'outbound'
log_data["tag"] = record.procedure_id.name
log_data["record"] = invoice
log_data["edi_event_id"] = record.id

try:
  response = requests.request(url=record.url, method=record.method,
                              headers=headers, data=request_content,
                              cert=cert_path)
  record.write({'state':'sent'})
  log_data["status_code"] = response.status_code
  log_data["reason"] = response.reason
  try:
    log_response = etree.tostring(etree.fromstring(response.content), pretty_print=True)
    log_data["response"] = log_response.decode()
    log_record = self.env['service.log'].register(**log_data)
    
    log_dict = log_record.get_response_dict()
    dMsgRes = log_dict.get("dMsgRes","")
    dCodRes = log_dict.get("dCodRes","")
    if dMsgRes == 'CDC encontrado':
      ivals = {}
      ivals["sifen_state"] = "approved"
      ivals["sifen_state_code"] = dCodRes
      ivals["sifen_state_message"] = dMsgRes
      pattern = r'<ns2:xContenDE>(.*?)</ns2:xContenDE>'
      elements = re.search(pattern,log_response.decode(),re.DOTALL)
      if elements:
        de_xml = html.unescape(elements.group(1))
        pattern = r"<dProtAut>(.*?)</dProtAut>"
        elements = re.search(pattern, de_xml,re.DOTALL)
        if elements:
          dProtAut = elements.group(1)
          ivals["sifen_authorization"] = dProtAut
      invoice.write(ivals)
      record.finish()
  except BaseException as errstr:
    log_response = response.content.decode()
    log_data["response"] = log_response
    log_record = self.env['service.log'].register(**log_data)
    
    _logger.error("Error parsing Response: %s..." % (errstr))
    # _logger.error(log_response)
except BaseException as errstr:
    _logger.error("Error on Request: %s..." % (errstr))
    
    log_data["response"] = errstr
    log_record = self.env['service.log'].register(**log_data)
