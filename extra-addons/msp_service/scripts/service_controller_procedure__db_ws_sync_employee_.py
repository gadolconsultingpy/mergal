# create_date: 2024-03-28 02:13:38.234652
# write_date: 2024-03-28 09:55:57.529465
# name: Empleados
# route: /db/ws/sync/employee

json_data = request.get_json_data()
partner_list = json_data.get("employee", [])

def process_get(self, param):
    code = param.get("code")
    _logger.info(param)
    partner = self.env['hr.employee'].search( [('barcode','=', code)] )
    if partner:
        vals = {}
        vals['code'] = partner.barcode
        vals['name'] = partner.name
        vals['status'] = "exists"
        return vals
    return {'error': {'code':'1', "message":"Employee Not Found: %s " %(vat)}}

def process_post(self, param):
    pvals = {}
    pvals['name'] = param.get('name')
    pvals['barcode'] = param.get('code')
    try:
      partner = self.env['hr.employee'].create(pvals)
      if partner:
        vals = {}
        vals['code'] = partner.barcode
        vals['name'] = partner.name
        vals['status'] = "new"
        return vals
      else:
        vals = {}
        vals["error"] = {'code':'2', "message":"Employee Creation Error: %s" %(partner)}
        return vals
    except BaseException as errstr:
      vals = {}
      vals["error"] = {'code':'3', "code":param.get("code"), "message":"Employee Creation Error: %s" %(errstr)}
      return vals

def check_request(self, request, param):
    response = {}
    # required fields
    rfields = ['code']
    if request.httprequest.method == "POST":
        rfields.append('name')
    for rf in rfields:
        if not param.get(rf, False):
            response["error"] = {"code": "1", "message": "Missing Required Field: %s" % (rf)}
            return response
    return True

response = {}
response['employee'] = []
for param in partner_list:
    check = check_request(self, request, param)
    _logger.info(["CHECK", param.get("vat"), check])
    if isinstance(check, bool) and check:
        if request.httprequest.method == "GET":
          res = process_get(self, param)
          response['employee'].append(res)
          _logger.info(["RESPONSE", response])
        elif request.httprequest.method == "POST":
            code = param.get("code")
            partner = self.env['hr.employee'].search([('barcode', '=', code)])
            if partner:
                res = process_get(self, param)
                response['employee'].append(res)
            else:
                res = process_post(self, param)
                response['employee'].append(res)
    else:
      response['employee'].append(check)
