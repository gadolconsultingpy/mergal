import html

from odoo import api, models, fields, _
# import logging
# _logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_escaped_name(self):
        # _logger.info("self, %s" % self)
        # _logger.info("self.id, %s" % self.id)
        # _logger.info("self.name, %s " % self.name)
        return html.escape(self.name)
