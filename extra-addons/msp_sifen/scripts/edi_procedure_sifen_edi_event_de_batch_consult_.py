# create_date: 2023-10-02 01:19:51.830800
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.edi.event.de_batch_consult
# comment: OK. Envia a la SIFEN la consulta del Lote

# record = edi.event
import requests
import json
import base64
import collections
import re
import xmltodict
from lxml import etree

# print("Record in edi.event: %s" %(record._name))

headers = json.loads(record.headers)
cert_path = self.env['edi.certificate'].prepare_cert_file(company_id=record.company_id.id, recreate=True)

edi_batch = self.env[record.res_model].search([('id', '=', record.res_id)])

request_content = base64.b64decode(record.request_content)

log_data = {}
log_data["method"] = record.soap_method
log_data["path"] = record.url
log_data["request"] = request_content.decode()
log_data["type"] = 'outbound'
log_data["tag"] = record.procedure_id.name
log_data["record"] = edi_batch
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
    log_data["response"] = log_response
    log_record = self.env['service.log'].register(**log_data)
  
    namespaces = {'ns2':None, 'env':None} 
    dd = xmltodict.parse(log_response, namespaces=namespaces)
    envelope = dict(dd.get("Envelope"))
    body = dict(envelope.get("Body"))
    batch = dict(body.get('rResEnviConsLoteDe'))
    
    dCodResLot = batch.get('dCodResLot')
    dMsgResLot = batch.get('dMsgResLot')

    pattern = r"Procesamiento de lote {\d+} concluido"
    match = re.match(pattern, dMsgResLot)
    if match:
      uvals = {}
      uvals['sifen_state'] = 'finish'
      uvals['sifen_state_code'] = dCodResLot
      uvals['sifen_state_message'] = dMsgResLot
      edi_batch.write(uvals)
    if dCodResLot == "0364":
      uvals = {}
      uvals['sifen_state'] = 'expire'
      uvals['sifen_state_code'] = dCodResLot
      uvals['sifen_state_message'] = dMsgResLot
      edi_batch.write(uvals)
      
    batch_response = batch.get('gResProcLote')
    if isinstance(batch_response, collections.OrderedDict):
      # print("D", type(batch_response), len(batch_response))
      response_list = [dict(batch_response)]
    else:
      response_list = batch_response
      # print("L", type(batch_response), len(batch_response))
    for response in response_list: 
      # response = dict(batch.get('gResProcLote'))
      cdc = response.get('id')
      dEstRes = response.get('dEstRes')
      dProtAut = response.get('dProtAut')
      if dEstRes in ['Aprobado','Rechazado']:
        message = dict(response.get('gResProc'))
        dCodRes = message.get('dCodRes')
        dMsgRes = message.get('dMsgRes')
        batch_record = None
        if edi_batch.move_type in ['out_invoice','out_refund']:
          batch_record = self.env['account.move'].search([('control_code','=',cdc)])
        elif edi_batch.move_type == 'stock_picking':
          batch_record = self.env['stock.picking'].search([('control_code','=',cdc)])  
        if batch_record:
          ivals = {}
          if dEstRes == 'Aprobado':
            ivals["sifen_state"] = 'approved'
          elif dEstRes == 'Rechazado':
            ivals["sifen_state"] = 'rejected'
          ivals["sifen_authorization"] = dProtAut
          ivals["sifen_state_code"] = dCodRes
          ivals["sifen_state_message"] = dMsgRes
          _logger.info("Updating Invoice: %s" %(ivals))
          batch_record.write(ivals)
  except BaseException as errstr:
    log_data["response"] = errstr
    log_record = self.env['service.log'].register(**log_data)
    
    _logger.error("Error parsing Response: %s" % (errstr))
    _logger.error(log_response)
except BaseException as errstr:
    _logger.error("Error on Request: %s" % (errstr))
    
    log_data["response"] = errstr
    log_record = self.env['service.log'].register(**log_data)
