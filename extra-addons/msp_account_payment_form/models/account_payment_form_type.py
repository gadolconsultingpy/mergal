from odoo import api, models, fields


class AccountPaymentFormType(models.Model):
    _name = "account.payment.form.type"
    _description = 'EDI Payment Type'

    name = fields.Char("Name")
    help_string = "CODIGOS PREDEFINIDOS:" \
                  "\n[cash] - Efectivo" \
                  "\n[check] -Cheque día" \
                  "\n[card] - Tarjeta" \
                  "\n[deferred-check] - Cheque Adelantado" \
                  "\n[voucher] - Vale" \
                  "\n[bank] - Banco" \
                  "\n[other] - Otro"
    code = fields.Char("Code", help=help_string)
