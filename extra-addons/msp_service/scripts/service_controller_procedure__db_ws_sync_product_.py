# create_date: 2024-04-01 19:18:51.429084
# write_date: 2024-04-01 19:19:51.428994
# name: Productos
# route: /db/ws/sync/product

response = {}
response["product"] = []

request_json = request.get_json_data()
product_list = request_json.get("product",[])

def check_request(self, param, idx):
  code = param.get('code', False)
  if not code:
    return {'error':{'code':"10000", 'message':'Missing Field Code: Element %s' %(idx) }}
  return True

def process_get(self, param):
  code = param.get('code')
  prod = self.env['product.product'].search([('default_code', '=', code)], limit=1)
  if prod:
    return {'code':code, 'name':prod.name, 'state':'exists'}
  return {'error':{'code':"10001", 'message':'Product does not exists: %s' %(code)}}

for idx, prod in enumerate(product_list,start=1):
  check_res = check_request(self, prod, idx)
  if not isinstance(check_res, bool):
    response["product"].append(check_res)
    
  if request.httprequest.method == "GET":
    prod_res = process_get(self, prod)
    response["product"].append(prod_res)
  elif request.httprequest.method == "POST":
      code = prod.get('code')
      check_prod = self.env['product.product'].search([('default_code', '=', code)], limit=1)
      if check_prod:
        prod_res = process_get(self, prod)
        response["product"].append(prod_res)
      else:
        pvals = {}
        pvals['name'] = prod.get('name')
        pvals['default_code'] = prod.get('code')
        pvals['barcode'] = prod.get('barcode')
        pvals['uom_id'] = self.env['uom.uom'].search([('symbol', '=', prod.get('unit_code'))]).id
        pvals['uom_po_id'] = self.env['uom.uom'].search([('symbol', '=', prod.get('unit_code'))]).id
        product = self.env['product.product'].create(pvals)
        response["product"].append({'code':code, 'name':product.name, 'state':'new'})