from odoo import api, models, fields


class EDITransactionType(models.Model):
    _name = 'edi.transaction.type'
    _description = "Electronic Transaction Type"

    code = fields.Char("Code")
    name = fields.Char("Name")
    note = fields.Text("Note")