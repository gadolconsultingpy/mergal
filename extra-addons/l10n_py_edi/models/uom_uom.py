from odoo import api, models, fields

class UomUom(models.Model):
    _inherit = 'uom.uom'

    code = fields.Char("Code")
    symbol = fields.Char("Symbol")

