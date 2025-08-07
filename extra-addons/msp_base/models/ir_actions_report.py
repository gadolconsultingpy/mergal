from odoo import api, models, fields, _


class IrActionReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def format_value(self, value, currency_id=None, symbol=False, decimal_precision=""):
        currency_id = currency_id or self.env.company.currency_id.id
        curr = self.env['res.currency'].browse(currency_id)
        decimal_places = curr.decimal_places
        if decimal_precision:
            dp = self.env['decimal.precision'].search([('name', '=', decimal_precision)], limit=1)
            decimal_places = dp.digits if dp else decimal_places
        if curr:
            if curr.position == 'after':
                format_str = "{:,.%sf} %s" % (decimal_places, " %s" % (curr.symbol if symbol else ""))
            else:
                format_str = "%s {:,.%sf}" % (" %s" % (curr.symbol if symbol else ""), decimal_places)
        else:
            format_str = "{:,.2f}"
        return format_str.format(value).replace(",", ":").replace(".", ",").replace(":", ".")
