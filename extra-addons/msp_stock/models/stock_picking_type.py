from odoo import api, models, fields, _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    select_existing_lots = fields.Boolean(string='Select Lot Names on Delivery Orders', default=False,
                                          help='If enabled, when validating delivery orders for products with lot/serial number tracking, '
                                               'a wizard will prompt to enter the lot/serial numbers to be used.')
