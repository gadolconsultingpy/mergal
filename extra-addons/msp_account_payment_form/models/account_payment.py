from odoo import _, api, models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    move_payment_form_id = fields.Many2one('account.move.payment.form', string="Invoice Payment Form")

    # Payment Form
    payment_form_id = fields.Many2one('account.payment.form', string="Payment Form")
    payment_form_type = fields.Selection(related='payment_form_id.type', string="Payment Form Type")
    payment_bank_id = fields.Many2one('res.bank', string="Bank")
    payment_number = fields.Char("Payment Number")
    transfer_number = fields.Char("Transfer Number")
    require_number = fields.Boolean('Require Number', related='payment_form_id.require_number')

    @api.onchange('payment_form_id')
    def _onchange_payment_form_id_payment(self):
        if self.payment_form_id and not self.payment_form_id.journal_id:
            message = _("Missing Journal in Payment Form!")
            return {'warning':
                        {'title'  : _('Configuration Error'),
                         'message': message},
                    'value'  : {}}
        self.journal_id = self.payment_form_id.journal_id.id
        if self.payment_type == 'inbound':
            self.payment_method_line_id = self.payment_form_id.payment_method_inbound_id.id
        elif self.payment_type == 'outbound':
            self.payment_method_line_id = self.payment_form_id.payment_method_outbound_id.id
        if self.payment_form_type == 'bank':
            if self.payment_form_id.bank_id:
                self.payment_bank_id = self.payment_form_id.bank_id.id
            else:
                message = _("Missing Bank in Payment Form!")
                return {'warning':
                            {'title'  : _('Configuration Error'),
                             'message': message},
                        'value'  : {}}
