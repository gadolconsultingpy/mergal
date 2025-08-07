from odoo import api, models, fields, _


class AccountDocumentType(models.Model):
    _name = 'account.document.type'
    _description = "Document Type"

    code = fields.Char("Code")
    name = fields.Char("Name")
    purchases = fields.Boolean("Purchase")
    sales = fields.Boolean("Sales")
    income = fields.Boolean("Income")
    expenses = fields.Boolean("Expenses")
    tax_report = fields.Boolean("Tax Report", help="Include in Tax Report")
    stamped_control = fields.Boolean("Stamped Control")
