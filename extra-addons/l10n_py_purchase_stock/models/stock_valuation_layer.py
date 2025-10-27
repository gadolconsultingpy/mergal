from odoo import api, models, fields, _


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    def action_update_unit_price(self):
        pass

    def action_validate_accounting_entries(self):
        """ Overridden to set amount_currency to 0 in case of valuation layer generated from
            purchase move having an account move line already created.
        """
        for svl in self:
            if not svl.account_move_id:
                print("Custom Validation of Accounting Entries for SVL: %s" % svl.id)
                svl._validate_accounting_entries()
