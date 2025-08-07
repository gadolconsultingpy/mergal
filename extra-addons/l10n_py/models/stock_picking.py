from odoo import api, models, fields, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sequence_id = fields.Many2one('ir.sequence', string="Picking Sequence")
