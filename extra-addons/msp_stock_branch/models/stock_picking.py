from odoo import api, models, fields, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_branch(self):
        if self.env.user.branch_id:
            return self.env.user.branch_id
        return None

    branch_id = fields.Many2one('res.branch', string="Branch", default=_get_branch)

    @api.onchange('picking_type_id')
    def _onchange_picking_type_branch(self):
        if self.branch_id:
            dp = self.branch_id.get_dispatch_point(move_type='stock_picking')
            if dp:
                self.sequence_id = dp.sequence_id.id
                self.journal_id = dp.sequence_id.journal_id.id
