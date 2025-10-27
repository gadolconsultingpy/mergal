from odoo import api, models, fields

class EDIDocumentType(models.Model):
    _name = 'edi.document.type'
    _description = 'Electronic Document Type'

    code = fields.Char("Code")
    name = fields.Char("Name")
    note = fields.Text("Note")
