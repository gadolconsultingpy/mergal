from odoo import api, models, fields

class AccountTaxType(models.Model):
    _name = 'account.tax.type'
    _description = 'Tax Type'

    code = fields.Char("Code")
    name = fields.Char("Name")
