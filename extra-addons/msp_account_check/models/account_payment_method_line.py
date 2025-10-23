from odoo import api, models, fields, _


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    check_type = fields.Selection(
            [
                ('check', 'Check'),
                ('deferred-check', 'Deferred Check')
            ], string="Check Type"
    )
