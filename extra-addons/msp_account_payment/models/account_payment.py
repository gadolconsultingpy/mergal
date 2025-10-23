from odoo import api, models, fields, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_origin = fields.Selection(
            [
                ('manual', 'Manual'),
            ], default='manual', string="Payment Origin"
    )
