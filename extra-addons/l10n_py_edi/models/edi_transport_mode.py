from odoo import api, models, fields, _


class EDITransportMode(models.Model):
    _name = 'edi.transport.mode'
    _description = 'EDI Transport Mode'

    name = fields.Char(string='Name', required=True, help='Name of the transport mode')
    code = fields.Char(string='Code', required=True, help='Code of the transport mode')
