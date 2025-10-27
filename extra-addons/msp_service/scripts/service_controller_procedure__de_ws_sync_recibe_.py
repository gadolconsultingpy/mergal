# create_date: 2024-04-01 19:18:51.429084
# write_date: 2024-04-01 19:19:51.428994
# name: Facturas
# route: /de/ws/sync/recibe



def check_request(self, json_data):
  invoice_data = json_data.get("invoice", {})
  invoice_header = invoice_data.get("header", {})
  sec_code = invoice_header.get("security_code")
  
  inv = self.env['account.move'].search([('security_code','=',sec_code)],limit=1)
  if inv:
    return {'error':{'code':'10013', 'message':'Security Code (%s) Used in Invoice (%s)' %(sec_code, inv.name)}}
  return True
  

def process_post(self, json_data):
  invoice_data = json_data.get("invoice", {})
  invoice_header = invoice_data.get("header", {})
  invoice_detail = invoice_data.get("detail", [])
  invoice_document = invoice_data.get("document", [])
  invoice_payment = invoice_data.get("payment", [])
  post = invoice_header.get('post',1)

  number = invoice_header.get("number")

  if invoice_header.get('document_type') == 1:
    invoice = self.env['account.move'].search([('name','=',number),('move_type','=','out_invoice')])
  if invoice_header.get('document_type') == 5:
    invoice = self.env['account.move'].search([('name','=',number),('move_type','=','out_refund')])
  if invoice:
    response = {"error":{"code":"10000", "message":"Invoice Already Exists: id %s" %(invoice.id)}}
    return response

  hvals = {}
  hvals['company_id'] = self.env.company.id
  
  ##### PARTNER
  partner = self.env['res.partner'].search([('vat','=',invoice_header.get("partner_vat")),('parent_id','=',False)],limit=1,order="id")
  if not partner:
    response = {"error":{"code":"10001", "message":"Partner Not Found: %s" %(invoice_header.get("partner_vat"))}}
    return response
  hvals['partner_id'] = partner.id
  
  ##### CURRENCY
  currency = self.env['res.currency'].search([('name','=',invoice_header.get("currency_code"))],limit=1,order="id")
  if not currency:
    response = {"error":{"code":"10002", "message":"Currency Not Found: %s" %(invoice_header.get("currency_code"))}}
    return response
  hvals['currency_id'] = currency.id
  hvals['inverse_rate'] = invoice_header.get("exchange_rate")

  ##### BRANCH
  branch = self.env['res.branch'].search([('code','=',invoice_header.get("branch_code"))],limit=1,order="id")
  if not branch:
    response = {"error":{"code":"10003", "message":"Branch Not Found: %s" %(invoice_header.get("branch_code"))}}
    return response
  hvals['branch_id'] = branch.id

  ##### PAYMENT TERM
  payment_term = self.env['account.payment.term'].search([('code','=',invoice_header.get("payment_term"))])
  if not payment_term:
    response = {"error":{"code":"10008", "message":"Payment Term Not Found: %s" %(invoice_header.get("payment_term"))}}
    return response
  hvals['invoice_payment_term_id'] = payment_term.id
  
  ### PAYMENT FORMS
  if payment_term.credit_type == "0":
    payment_form_lines = [(5,0,0)]
    for pay in invoice_payment:
      pvals = {}
      pvals['payment_form_id'] = self.env['account.payment.form'].search([('code','=',pay.get('type'))]).id
      pvals['payment_currency_id'] = self.env['res.currency'].search([('name','=',pay.get("currency_code"))],limit=1,order="id").id
      pvals['payment_amount'] = pay.get('amount')
      if hvals['currency_id'] != pvals['payment_currency_id']:
        pvals['payment_currency_rate'] = pay.get('exchange_rate')
        pvals['amount'] = pvals['payment_amount'] * pvals['exchange_rate']
      else:
        pvals['payment_currency_rate'] = 1.0
        pvals['amount'] = pay.get('amount')
      payment_form_lines.append((0,0,pvals))
    hvals['payment_form_ids'] = payment_form_lines

  ##### EMISSION TYPE
  emission_type = invoice_header.get("emission_type")
  hvals['issue_type'] = str(emission_type)

  ##### SECURITY CODE
  hvals['security_code'] = invoice_header.get("security_code")

  ##### SEQUENCE
  hvals['name'] = invoice_header.get("number")
  if invoice_header.get('document_type') == 1:
    move_type = "out_invoice"
  if invoice_header.get('document_type') == 5:
    move_type = "out_refund"
  hvals['move_type'] = move_type
  number_prefix = invoice_header.get("number_prefix")
  dp = branch.get_prefix_dispatch_point(prefix=number_prefix, move_type=move_type)
  if not dp:
    response = {"error":{"code":"10004", "message":"Sequence Prefix Not Found: %s" %(number_prefix)}}
    return response
  hvals['sequence_id'] = dp.sequence_id.id
  hvals['journal_id'] = dp.journal_id.id

  if move_type == 'out_refund':
    credit_reason = invoice_header.get('credit_reason')
    hvals['issue_reason_id'] = self.env['edi.issue.reason'].search([('code','=',credit_reason)]).id
    hvals['reverted_invoice_ids'] = [(5,0,0)]
    for doc in invoice_document:
      cvals = {}
      _logger.info([doc.get('credit_type'), type(doc.get('credit_type'))])
      if doc.get('credit_type') == 1:
        _logger.info("credit_type_1")
        cvals['reversion_document_type'] = str(doc.get("credit_type"))
        cvals['reverted_cdc'] = doc.get("cdc")
      if doc.get('credit_type') == 2:
        _logger.info("credit_type_2")
        cvals['reversion_document_type'] = str(doc.get("credit_type"))
        cvals['reverted_stamped_number'] = doc.get("stamped_number")
        cvals['reverted_invoice_establishment'] = doc.get("establishment")
        cvals['reverted_invoice_dispatch_point'] = doc.get("dispatch_point")
        cvals['reverted_invoice_number'] = doc.get("document_number")
        cvals['reverted_invoice_date'] = doc.get("invoice_date")
        cvals['reverted_invoice_type_id'] = self.env['edi.document.type'].search([('code','=',doc.get('document_type'))]).id
      hvals['reverted_invoice_ids'].append((0,0,cvals))
    
  hvals['invoice_date'] = invoice_header.get("invoice_date")

  hvals['invoice_line_ids'] = []
  for item in invoice_detail:
    code = item.get('product_code')
    if not code:
      response = {"error":{"code":"10005", "message":"Product Code Missing"}}
      return response
    product = self.env['product.product'].search([('default_code','=',code)])
    if not product:
      response = {"error":{"code":"10006", "message":"Product Not Found: %s" %(item.get('product_code'))}}
      return response
    ivals = {}
    ivals['product_id'] = product.id
    ivals['account_id'] = product.categ_id.property_account_income_categ_id.id
    ivals['name'] = product.name
    ivals['quantity'] = item.get("quantity")
    ivals['price_unit'] = item.get("price_unit")
    hvals['invoice_line_ids'].append((0,0,ivals))

  _logger.info("INVOICE VALS: %s" %(hvals) )
  _logger.info("Creating Invoice")
  try:
    invoice = self.env['account.move'].create(hvals)
  except BaseException as errstr:
    response = {"error":{"code":"10010", "message":"Error creating Invoice: %s" %(errstr) }}
    return response
  _logger.info("Checking Total")
  if invoice:
    if invoice.amount_total != invoice_header.get('total'):
        response = {"error":{"code":"10007", "message":"Invoice Total are different %s <> %s " %(invoice.amount_total, invoice_header.get("total")) }}
        invoice.write({'name':False})
        invoice.unlink()
        return response
  _logger.info("Checking CDC")
  if invoice:
    calc_cdc = invoice.get_code_of_control()
    cdc = invoice_header.get('cdc')
    if cdc != calc_cdc:
      response = {"error":{"code":"10012", "message":"CDC calculated (%s) does not match with CDC received (%s)" %(calc_cdc, cdc) }}
      invoice.write({'name':False})
      invoice.unlink()
      return response
  _logger.info("Posting Invoice")
  if invoice:
    try:
      invoice.action_post()
    except BaseException as errstr:
      response = {"error":{"code":"10009", "message":"Cannot Confirm Invoice: %s" %(errstr)}}
      # invoice.write({'name':False})
      # invoice.unlink()
      return response
  response = {"invoice_id":invoice.id, "cdc":invoice.control_code}
  return response

json_data = request.get_json_data()

check_res = check_request(self, json_data)
if not isinstance(check_res,bool):
  response = check_res
else:
  if request.httprequest.method == "POST":
    response = process_post(self, json_data)
              