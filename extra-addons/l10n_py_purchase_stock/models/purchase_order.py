from odoo import api, models, fields, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _get_stock_move_price_unit(self):
        self.ensure_one()
        order = self.order_id
        price_unit = self.price_unit
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        if self.taxes_id:
            qty = self.product_qty or 1
            price_unit = self.taxes_id.compute_all(
                    price_unit,
                    currency=self.order_id.currency_id,
                    quantity=qty,
                    product=self.product_id,
                    partner=self.order_id.partner_id,
                    rounding_method="round_globally",
            )['total_void']
            price_unit = price_unit / qty
        if self.product_uom.id != self.product_id.uom_id.id:
            price_unit *= self.product_uom.factor / self.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            ##### Aply the custom inverse rate to set stock_move price unit #####
            ctx = self.env.context.copy()
            ctx['custom_currency_rate'] = order.inverse_rate
            price_unit = order.currency_id.with_context(ctx)._convert(
                    price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(),
                    round=False)
        return float_round(price_unit, precision_digits=price_unit_prec)
