from odoo import api, models, fields, _


class IrDefault(models.Model):
    _inherit = 'ir.default'

    account_id = fields.Many2one('account.account', string='Account', domain="[('company_id', '=', company_id)]")
