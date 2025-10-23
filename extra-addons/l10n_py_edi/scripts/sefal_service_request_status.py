import requests
import time
import json
import logging

_logger = logging.getLogger(__name__)

filters = []
filters.append(('move_type', 'in', ['out_invoice', 'out_refund']))
filters.append(('sifen_state', '=', 'pending'))

documents = self.env['account.move'].search(filters)
# for dd in documents:
# print(dd.name)
cdcs = [x.control_code for x in documents]
_logger.info("CDCs to Check: %s" % (len(cdcs)))

cdc_list = {"cdcs": cdcs}

payload = {}
payload["datajson"] = json.dumps(cdc_list)

# print("PAYLOAD", payload)

url = 'http://localhost:5080/sifen/v2/estadoDE.php'
method = "POST"
try:
    response = requests.request(method, url, data=payload)

    # print("RESPONSE", response.content.decode())

    response_obj = json.loads(response.content.decode())
    # print("RESPONSE_OBJ", response_obj)
except BaseException as errstr:
    print("Error 1: %s - %s - %s " % (url, method, errstr))

try:
    trans_state = {}
    trans_state["Aprobado"] = 'approved'
    trans_state["Rechazado"] = 'rejected'
    trans_state["No encontrado"] = 'pending'

    for ss in response_obj:
        print(ss)
        amove = self.env['account.move'].search([('control_code', '=', ss.get("cdc"))])
        if amove:
            vals = {}
            vals['sifen_state'] = trans_state.get(ss.get('estado', 'No encontrado'))
            vals['sifen_state_message'] = ss.get('mensaje', '')
            amove.write(vals)
except BaseException as errstr:
    print("Error 2: %s - %s - %s " % (url, method, errstr))

try:
    vlog = {}
    vlog['path'] = url
    vlog['method'] = method
    vlog['request'] = payload
    vlog['response'] = response.content.decode()
    vlog['type'] = 'outbound'
    vlog['tag'] = 'sefal.service.request.status'
    log = self.env['service.log']
    log.register(**vlog)
    # self.env.cr.commit()
except BaseException as errstr:
    print("Error 3: %s - %s - %s " % (url, method, errstr))


