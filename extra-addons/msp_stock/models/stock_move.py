from odoo import api, models, fields, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    display_select_lot = fields.Boolean(string='Display Select Lot',
                                        compute='_compute_display_select_lot')

    @api.depends('product_id', 'picking_type_id')
    def _compute_display_select_lot(self):
        for move in self:
            move.display_select_lot = False
            if move.picking_type_id and move.picking_type_id.code == 'outgoing' and move.picking_type_id.select_existing_lots:
                if move.product_id and move.product_id.tracking != 'none':
                    move.display_select_lot = True

    def select_lots(self):
        record = self.env['stock.move.select.lots'].create({'move_id': self.id})
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Select Lots'),
            'res_model': 'stock.move.select.lots',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : record.id,
        }
