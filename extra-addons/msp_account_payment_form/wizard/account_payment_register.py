from odoo import api, models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_form_id = fields.Many2one('account.payment.form', string="Payment Form")
    payment_form_type = fields.Selection(related='payment_form_id.type', string="Payment Form Type")
    move_payment_form_id = fields.Many2one('account.move.payment.form', string="Invoice Payment Form")

    payment_bank_id = fields.Many2one('res.bank', string="Bank")
    transfer_number = fields.Char("Transfer Number")

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals['payment_form_id'] = self.payment_form_id.id
        payment_vals['move_payment_form_id'] = self.move_payment_form_id.id
        payment_vals['payment_bank_id'] = self.payment_bank_id.id
        payment_vals['transfer_number'] = self.transfer_number
        return payment_vals

    @api.onchange('payment_form_id')
    def _onchange_payment_form_id_form(self):
        if self.payment_form_id:
            self.journal_id = self.payment_form_id.journal_id.id
            self.payment_bank_id = self.payment_form_id.bank_id.id
            if self.payment_type == 'inbound':
                self.payment_method_line_id = self.payment_form_id.payment_method_inbound_id.id
            if self.payment_type == 'outbound':
                self.payment_method_line_id = self.payment_form_id.payment_method_outbound_id.id
