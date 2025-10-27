from odoo import _, fields, models, api
import logging
import jinja2

_logger = logging.getLogger(__name__)


class RecConfigCustom(models.Model):
    _inherit = 'res.config.custom'

    skip_cash_payment_create = fields.Boolean("Skip Cash Payment Creation", default=False)
    cash_payment_form_id = fields.Many2one('account.payment.form', string="Cash Payment Form")
