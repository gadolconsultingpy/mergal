from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder,self)._create_invoices(grouped=grouped, final=final, date=date)
        for mv in moves:
            mv._onchange_l10n_py_currency()
            mv._set_sequence_id()
        return moves
