from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    issue_date = fields.Date('Issue Date')
    accreditation_date = fields.Date("Accreditation Date")
    check_number = fields.Char("Check Number")
    checkbook_id = fields.Many2one('account.checkbook', string="Checkbook")
    payment_bank_id = fields.Many2one('res.bank', string="Issue Bank")
    payment_method_check_type = fields.Selection(related='payment_method_line_id.check_type',
                                                 string="Payment Method Check Type")

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result=batch_result)
        if self.issue_date and self.accreditation_date:
            if self.accreditation_date < self.issue_date:
                raise ValidationError(_("Accreditation Date can not be prior than Issue Date"))
        payment_vals['issue_date'] = self.issue_date
        payment_vals['accreditation_date'] = self.accreditation_date
        payment_vals['checkbook_id'] = self.checkbook_id.id
        payment_vals['check_number'] = self.check_number
        payment_vals['payment_bank_id'] = self.payment_bank_id.id
        payment_vals['payment_method_check_type'] = self.payment_method_check_type
        return payment_vals

    @api.onchange('payment_method_line_id')
    def _onchange_journal_payment_method_line_id(self):
        if self.payment_method_line_id.check_type in ['check', 'deferred-check']:
            self.payment_bank_id = self.journal_id.bank_id.id
        if not self.journal_id.bank_id:
            self.payment_bank_id = False
