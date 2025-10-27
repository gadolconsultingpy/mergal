import uuid
import json
import requests
from odoo import fields

service = self.env['sefal.service'].search([('name', '=', 'account.move.send')])
if service:
    url = service.url
    method = service.method

    invoice = record
    print(invoice.name, invoice.id)
    print(f"Processing Invoice {invoice} with {service.name}")
    data = {}
    data['fecha'] = fields.Datetime.context_timestamp(invoice, invoice.create_date).strftime("%Y-%m-%d %H:%M:%S")
    data['cdcAsociado'] = ""
    number_data = invoice.name.split("-")
    data['establecimiento'] = number_data[0]
    data['punto'] = number_data[1]
    data['numero'] = number_data[2]
    data['descripcion'] = ""
    data['moneda'] = invoice.currency_id.name
    data['tipoDocumento'] = 1
    data['tipoEmision'] = 1
    data['tipoTransaccion'] = 1
    data['receiptid'] = invoice.sefal_uuid
    data['cliente'] = {
        'ruc'   : invoice.partner_id.vat,
        'nombre': invoice.partner_id.name,
        'cpais' : invoice.partner_id.country_id.iso_code
    }
    data['codigoSeguridadAleatorio'] = invoice.security_code
    data['items'] = []
    for line in invoice.invoice_line_ids:
        data['items'].append({
            'descripcion'   : line.product_id.name,
            'codigo'        : line.product_id.default_code,
            'tipoIva'       : line.tax_ids[0].name,
            'unidadMedida'  : line.product_uom_id.code,
            'ivaTasa'       : line.tax_ids[0].amount,
            'ivaAfecta'     : 1,
            'cantidad'      : line.quantity,
            'precioUnitario': invoice.currency_id.round(line.price_total / line.quantity),
            'precioTotal'   : line.price_total,
            'baseGravItem'  : line.price_total - (line.price_total - line.price_subtotal),
            'liqIvaItem'    : line.price_total - line.price_subtotal
        })
    data['pagos'] = []
    data['condicionPago'] = int(invoice.invoice_payment_term_id.credit_type)
    for payment in invoice.payment_form_ids:
        pvals = {}
        pvals['name'] = payment.payment_form_id.name
        pvals['tipoPago'] = payment.payment_form_id.code
        pvals['monto'] = payment.amount
        data['pagos'].append(pvals)
    if invoice.payment_type == "2":
        data['credito'] = {}
        data['credito']['condicionCredito'] = int(invoice.invoice_payment_term_id.credit_type)
        data['credito']['descripcion'] = invoice.invoice_payment_term_id.name
        if invoice.invoice_payment_term_id.credit_type == "2":
            data['credito']['cantidadCuotas'] = len(invoice.installment_ids)
            data['credito']['cuotas'] = []
            for inst in invoice.installment_ids:
                data['credito']['cuotas'].append(
                        {
                            'numero': inst.name,
                            'monto' : inst.amount,
                            'fecha' : inst.date_due.strftime("%Y-%m-%d"),
                        })
    data['totalPago'] = invoice.amount_total
    data['totalRedondeo'] = 0
    data['codigo'] = 1222
    data['pais'] = invoice.currency_id.name  # "PYG"

    payload = {}
    payload['datajson'] = json.dumps(data)
    payload['recordID'] = "123"

    response = requests.request(method, url, data=payload)

    log_data = {}
    log_data["method"] = method
    log_data["path"] = url
    log_data["request"] = json.dumps(data, indent=4)
    log_data["type"] = 'outbound'
    log_data["tag"] = 'account.move.send'
    log_data["record"] = invoice
    log_data["response"] = response.content.decode()
    self.env['service.log'].register(**log_data)

    try:
        response_dict = json.loads(response.content.decode())
        if response_dict.get('status') == True:
            uvals = {}
            uvals['sefal_state'] = 'sent'
            uvals['control_code'] = response_dict.get('cdc')
            uvals['sifen_state'] = 'pending'
            uvals['sifen_state_message'] = ''
            link = response_dict.get('link')
            invoice.write(uvals)
            invoice.message_post(
                body='Consulte el documento en la SET haciendo <a href="%s" target="new" ><strong>click aquí</strong></a>' % (
                    link))
    except BaseException as errstr:
        print(errstr)
