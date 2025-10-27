from odoo import api, models, fields, _


class EDITransportType(models.Model):
    _name = 'edi.transport.type'
    _description = 'EDI Transport Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
