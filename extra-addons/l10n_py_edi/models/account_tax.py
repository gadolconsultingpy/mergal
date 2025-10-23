from odoo import api, models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_application_type_id = fields.Many2one('account.tax.application.type', string="Affectation Type")
    tax_type_id = fields.Many2one('account.tax.type', string="EDI Tax Type")
    code = fields.Char("Tax Code")