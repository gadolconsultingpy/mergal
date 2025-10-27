from odoo import api, models, fields

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    require_payment_form = fields.Boolean('Require Payment Form', help="For Immediate Payment")

    @api.onchange('require_payment_form')
    def _onchange_require_payment_form(self):
        if self.require_payment_form:
            self.credit_type = '0'