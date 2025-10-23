# create_date: 2024-04-01 19:18:51.429084
# write_date: 2024-04-01 19:19:51.428994
# name: Contactos
# route: /db/ws/sync/partner

json_data = request.get_json_data()
partner_list = json_data.get("partner", [])

def process_get(self, param):
    vat = param.get("vat")
    _logger.info(param)
    partner = self.env['res.partner'].search( [('vat','=', vat)] )
    if partner:
        vals = {}
        vals['code'] = partner.ref
        vals['vat'] = partner.vat
        vals['name'] = partner.name
        vals['status'] = "exists"
        return vals
    return {'error': {'code':'1', "message":"Partner Not Found: %s " %(vat)}}

def process_post(self, param):
    pvals = {}
    pvals['name'] = param.get('name')
    pvals['vat'] = param.get('vat')
    pvals['tax_payer_type'] = str(param.get('tax_payer_type'))
    if param.get('id_type',False):
      id_type = self.env['l10n_latam.identification.type'].search([('code','=',param.get('id_type'))])
      if id_type:
        pvals['l10n_latam_identification_type_id'] = id_type.id
    pvals['ref'] = param.get('code', "")
    pvals['phone'] = param.get('phone', "")
    pvals['mobile'] = param.get('mobile', "")
    pvals['email'] = param.get('email', "")
    pvals['street_name'] = param.get('address_street')
    pvals['street_number'] = param.get('address_number')
    try:
      partner = self.env['res.partner'].create(pvals)
      if partner:
        vals = {}
        vals['vat'] = partner.vat
        vals['code'] = partner.ref
        vals['name'] = partner.name
        vals['status'] = "new"
        return vals
      else:
        vals = {}
        vals["error"] = {'code':'2', "message":"Partner Creation Error: %s" %(partner)}
        return vals
    except BaseException as errstr:
      vals = {}
      vals["error"] = {'code':'3', "vat":param.get("vat"), "message":"Partner Creation Error: %s" %(errstr)}
      return vals

def check_request(self, request, param):
    response = {}
    # required fields
    rfields = ['vat']
    if request.httprequest.method == "POST":
        rfields.append('name')
    for rf in rfields:
        if not param.get(rf, False):
            response["error"] = {"code": "1", "message": "Missing Required Field: %s" % (rf)}
            return response
    id_type = param.get("id_type", False)
    if not id_type:
      check_vat = self.env['res.partner'].check_vat_py(param.get('vat'))
      if not check_vat:
        response["error"] = {"code": "3", "message": "Error in VAT Number Format: %s" % (param.get("vat"))}
        return response
    return True

response = {}
response['partner'] = []
for param in partner_list:
    check = check_request(self, request, param)
    _logger.info(["CHECK", param.get("vat"), check])
    if isinstance(check, bool) and check:
        if request.httprequest.method == "GET":
          res = process_get(self, param)
          response['partner'].append(res)
          _logger.info(["RESPONSE", response])
        elif request.httprequest.method == "POST":
            vat = param.get("vat")
            partner = self.env['res.partner'].search([('vat', '=', vat)])
            if partner:
                res = process_get(self, param)
                response['partner'].append(res)
            else:
                res = process_post(self, param)
                response['partner'].append(res)
    else:
      response['partner'].append(check)
