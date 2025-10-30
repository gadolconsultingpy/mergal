from odoo import api, models, fields, _


class StockMoveSelectLots(models.TransientModel):
    _name = 'stock.move.select.lots'
    _description = 'Wizard to select lots for a stock move'

    move_id = fields.Many2one('stock.move', string='Stock Move', required=True)
    product_id = fields.Many2one(related='move_id.product_id', string='Product')
    product_uom_qty = fields.Float(related='move_id.product_uom_qty', string='Quantity to Move')
    location_id = fields.Many2one(related='move_id.location_id', string='Source Location')
    lot_names = fields.Text(string='Lot Names')
    lot_ids = fields.Many2many('stock.quant', string='Lots')

    @api.onchange('lot_names')
    def _onchange_lot_names(self):
        if self.lot_names:
            lot_names = []
            if "\n" in self.lot_names:
                lot_names = [name.strip() for name in self.lot_names.split('\n') if name.strip()]
            elif "," in self.lot_names:
                lot_names = [name.strip() for name in self.lot_names.split(',') if name.strip()]
            else:
                lot_names = [self.lot_names.strip()]
            print(lot_names)
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.product_id.id),
                ('lot_id.name', 'in', lot_names),
                ('location_id', '=', self.location_id.id),
                ('available_quantity', '>', 0)
            ])
            print(quants)
            self.lot_ids = quants

    def action_confirm(self):
        smlids = []
        for lot_id in self.lot_ids:
            smlids.append((0,0, {'quant_id': lot_id.id, 'quantity':1}))
        self.move_id.move_line_ids = smlids