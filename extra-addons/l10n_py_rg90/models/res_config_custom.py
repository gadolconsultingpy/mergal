from odoo import _, fields, models, api
import logging

_logger = logging.getLogger(__name__)


class RecConfigCustom(models.Model):
    _inherit = 'res.config.custom'

    out_invoice_doc_type_id = fields.Many2one('account.document.type', string="Out Invoice Document Type",
                                              domain=[('sales', '=', True)])
    out_refund_doc_type_id = fields.Many2one('account.document.type', string="Out Refund Document Type",
                                             domain=[('sales', '=', True)])
    in_invoice_doc_type_id = fields.Many2one('account.document.type', string="In Invoice Document Type",
                                             domain=[('purchases', '=', True)])
    in_refund_doc_type_id = fields.Many2one('account.document.type', string="In Refund Document Type",
                                            domain=[('purchases', '=', True)])
