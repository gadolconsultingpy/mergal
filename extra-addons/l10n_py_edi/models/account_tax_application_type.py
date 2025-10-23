from odoo import api, models, fields

class AccountTaxApplicationType(models.Model):
    _name = 'account.tax.application.type'
    _description = 'Tax Application Type'

    code = fields.Char("Code")
    name = fields.Char("Name")
