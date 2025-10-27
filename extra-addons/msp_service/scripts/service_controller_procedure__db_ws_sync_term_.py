# create_date: 2024-04-01 19:18:51.429084
# write_date: 2024-04-01 19:19:51.428994
# name: Plazos de Pago
# route: /db/ws/sync/term

response = {}
error = False

json_data = request.get_json_data()
param = json_data.get("payment_term", {})

##### GET, POST ##### 
def process_get(self, param):
  response = {}
  code = param.get('code','')
  payment_term = self.env['account.payment.term'].search([('code', '=', code)])
  if payment_term:
    vals = {}
    vals['code'] = payment_term.code
    vals['name'] = payment_term.name
    vals['status'] = "exists"
    response["payment_term"] = vals
    return response
  else:
    response["error"] = {"code": "2", "message": "Payment Term does not exists: %s" %(code)}
    return response

def process_post(self, param):
  response = {}
  pvals = {}
  pvals['code'] = param.get('code')
  pvals['name'] = param.get('name')
  pvals['credit_type'] = param.get('credit_type')
  pvals['note'] = param.get('name')
  ##### check on post
  if pvals['credit_type'] == "0":
    pvals['require_payment_form'] = True
  elif pvals['credit_type'] == "1":
    pvals['require_payment_form'] = False
    pm_lines = param.get("lines")
    if len(pm_lines) > 1:
      response["error"] = {"code": "4", "message": "Credit Type 1 does not allow more than 1 lines"}
      return response
    pvals['line_ids'] = [(5,0,0)]
    line = pm_lines[0]
    plvals = {}
    plvals['value'] = line.get('type','balance')
    plvals['value_amount'] = line.get('value',0)
    plvals['months'] = line.get('months',0)
    plvals['days'] = line.get('days',0)
    pvals['line_ids'].append((0,0,plvals))
  elif pvals['credit_type'] == "2":
    pvals['require_payment_form'] = False
    pm_lines = param.get("lines")
    pvals['line_ids'] = [(5,0,0)]
    for line in pm_lines:
      plvals = {}
      plvals['value'] = line.get('type','balance')
      plvals['value_amount'] = line.get('value',0)
      plvals['months'] = line.get('months',0)
      plvals['days'] = line.get('days',0)
      pvals['line_ids'].append((0,0,plvals))

  payment_term = self.env['account.payment.term'].create(pvals)
  vals = {}
  vals['code'] = payment_term.code
  vals['name'] = payment_term.name
  vals['status'] = "new"
  response["payment_term"] = vals
  return response

def check_request(self, request, param):
  #required fields
  rfields = ['code']
  if request.httprequest.method == "POST":
    rfields.append('name')
  for rf in rfields:
    if not param.get(rf, False):
      response = {}
      response["error"] = {"code": "1", "message": "Missing Required Field: %s" %(rf)}
      return response
  return True

#####
response = check_request(self, request, param)
_logger.info("INSTANCE: %s" %([isinstance(response, bool), response]) )
if isinstance(response, bool) and response:
  if request.httprequest.method == "GET":
    response = process_get(self, param)
  elif request.httprequest.method == "POST":
    payment_term = self.env['account.payment.term'].search([('code', '=', param.get("code"))])
    if payment_term:
      response = process_get(self, param)
    else:
      response = process_post(self, param)