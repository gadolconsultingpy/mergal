from odoo import api, models, fields, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    invoice_currency_rate = fields.Float(string='Invoice Currency Rate', compute="_compute_invoice_currency_rate", )
    inverse_rate = fields.Float(string='User Inverse Rate', digits=(12, 6), default=1.0,
                                compute="_compute_inverse_rate", store=True)

    @api.depends('currency_id', 'company_currency_id', 'company_id', 'date_order')
    def _compute_inverse_rate(self):
        for porder in self:
            if porder.currency_id != porder.company_id.currency_id:
                currency_rate = self.env['res.currency']._get_conversion_rate(
                        from_currency=porder.company_currency_id,
                        to_currency=porder.currency_id,
                        company=porder.company_id,
                        date=porder._get_purchase_order_currency_rate_date(),
                )
            else:
                currency_rate = 1
            porder.inverse_rate = 1.0 / currency_rate or 1.0

    @api.depends('invoice_currency_rate', 'inverse_rate', 'currency_id')
    def _compute_invoice_currency_rate(self):
        for rec in self:
            if rec.currency_id != rec.company_id.currency_id:
                if rec.invoice_currency_rate:
                    rec.invoice_currency_rate = rec.currency_id._get_rates(self.company_id, rec.date_order).get(
                            rec.currency_id.id, 1.0)
                else:
                    rec.invoice_currency_rate = 1.0 / rec.inverse_rate or 1.0
            else:
                rec.invoice_currency_rate = 1.0

    def _get_purchase_order_currency_rate_date(self):
        return self.date_order or fields.Date.today()
