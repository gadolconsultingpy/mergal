from odoo import api, models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Fields Help
    # petty_cash_id         :   completed when petty cash fixed fund is open
    #                           and expenses reposition advance payment generated
    # petty_cash_sheet_id   :   completen when petty cash fixed fund is replenished,ç
    #                           and fully applied to petty cash sheet
    payment_origin = fields.Selection(
            selection_add=[
                ('petty-cash', 'Petty Cash'),
            ], ondelete={'petty-cash': lambda self: self.write({'payment_origin': 'manual'})})
    petty_cash_id = fields.Many2one('petty.cash.definition', string="Petty Cash", ondelete='restrict', copy=False)
    petty_cash_sheet_id = fields.Many2one('petty.cash.sheet', string="Petty Cash Sheet", copy=False,
                                          ondelete='restrict')
    petty_cash_destination_account_id = fields.Many2one('account.account', string='Petty Cash Destination Account')

    def get_check_payment_origin(self):
        polist = super(AccountPayment, self).get_check_payment_origin()
        polist.append('petty-cash')
        return polist

    def action_draft(self):
        if self.petty_cash_sheet_id:
            petty_cash_sheet = self.env['petty.cash.sheet'].browse(self.petty_cash_sheet_id.id)
            petty_cash_sheet.write({'payment_state': 'unpaid'})
        return super(AccountPayment, self).action_draft()

    def action_post(self):  #OK
        for rec in self:
            if rec.petty_cash_sheet_id:
                petty_cash_sheet = rec.env['petty.cash.sheet'].browse(rec.petty_cash_sheet_id.id)
                petty_cash_sheet.write({'payment_state': 'paid'})
        return super(AccountPayment, self).action_post()

    @api.onchange('petty_cash_id')
    def _onchange_petty_cash_id(self):
        if self.petty_cash_id:
            self.petty_cash_destination_account_id = self.petty_cash_id.account_id.id
            self.destination_account_id = self.petty_cash_id.account_id.id
        else:
            self.petty_cash_destination_account_id = False
            super(AccountPayment, self)._compute_destination_account_id()

    # internal_transfer deprecated on 18 - Bank transactions and internal transfer reconciliation instead
    @api.depends('journal_id', 'partner_id', 'partner_type')
    def _compute_destination_account_id(self):
        for pay in self:
            if pay.petty_cash_destination_account_id:
                pay.destination_account_id = pay.petty_cash_destination_account_id.id
            else:
                super(AccountPayment, pay)._compute_destination_account_id()
