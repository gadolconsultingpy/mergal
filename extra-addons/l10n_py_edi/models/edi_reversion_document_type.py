from odoo import api, models, fields

class EDIReversionDocumentType(models.Model):
    _name = 'edi.reversion.document.type'
    _description = 'Reversion Document Type'

    code = fields.Char("Code")
    name = fields.Char("Name")
