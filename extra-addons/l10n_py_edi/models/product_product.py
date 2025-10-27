from odoo import api, models, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_type(self):
		# odooV16
        return self.type