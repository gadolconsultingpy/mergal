# create_date: 2025-06-06 14:27:55.222215
# write_date: 2025-08-22 12:35:03.886311
# name: sifen.edi.event.de_invalid
# comment: OK. Envia la solicitud de cancelación de un documento

# record = edi.event
import requests
import json
import base64
from lxml import etree

# print("Record in edi.event: %s" %(record._name))

headers = json.loads(record.headers)
cert_path = self.env['edi.certificate'].prepare_cert_file(company_id=record.company_id.id, recreate=True)

invalid_invoices = self.env[record.res_model].search([('id', '=', record.res_id)])

request_content = base64.b64decode(record.request_content)

log_data = {}
log_data["method"] = record.soap_method
log_data["path"] = record.url
log_data["request"] = request_content.decode()
log_data["type"] = 'outbound'
log_data["tag"] = record.procedure_id.name
log_data["record"] = invalid_invoices
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
        
        log_dict = log_record.get_response_dict()
        dEstRes  = log_dict.get("dEstRes", "")
        dProtAut = log_dict.get("dProtAut", "")
        dCodRes  = log_dict.get("dCodRes", "")
        dMsgRes  = log_dict.get("dMsgRes", "")
        if dEstRes in ("Aprobado","Rechazado"):
          uvals = {}
          if dEstRes == "Aprobado":
            uvals['sifen_state'] = 'approved'
          elif dEstRes == "Rechazado":
            uvals['sifen_state'] = 'rejected'
          uvals['sifen_state_code'] = dCodRes
          uvals['sifen_state_message'] = dMsgRes
          uvals['sifen_authorization'] = dProtAut
          invalid_invoices.write(uvals)
          if dEstRes == "Aprobado":
            for invoice in invalid_invoices.invoice_ids:
              ivals = {}
              ivals['sifen_state'] = 'invalid'
              ivals['sifen_state_code'] = dCodRes
              ivals['sifen_state_message'] = dMsgRes
              ivals['sifen_authorization'] = dProtAut
              invoice.write(ivals)
              if invoice.state == 'posted' and invoice.sifen_state != 'approved':
                  _logger.error("Document to Draft: %s" %(invoice.name))
                  invoice.button_draft()
              _logger.error("Canceling Document: %s" %(invoice.name))
              invoice.button_cancel()
          record.finish()
    except BaseException as errstr:
        log_response = response.content.decode()
        log_data["response"] = log_response
        log_record = self.env['service.log'].register(**log_data)
        
        _logger.error("Error parsing Response: %s" % (errstr))
        _logger.error(log_response)
except BaseException as errstr:
    _logger.error("Error on Request: %s" % (errstr))
    
    log_data["response"] = errstr
    log_record = self.env['service.log'].register(**log_data)
