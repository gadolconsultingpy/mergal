from odoo import api, models, fields


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    code = fields.Char("Code")