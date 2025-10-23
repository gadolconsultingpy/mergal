from odoo import api, models, fields, _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    edi_sequence_id = fields.Many2one('ir.sequence', string="EDI Sequence")
