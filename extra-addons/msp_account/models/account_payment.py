from odoo import api, models, fields, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def print_custom_report(self):
        return self.env.ref('msp_account.account_payment_custom_report_action').report_action(self)

    def get_user_signature(self):
        signature = self.env['res.signature'].search([('user_id', '=', self.create_uid.id)], limit=1)
        return signature.signature
