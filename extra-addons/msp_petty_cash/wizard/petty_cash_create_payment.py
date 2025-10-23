from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PettyCashCreatePayment(models.TransientModel):
    _name = 'petty.cash.create.payment'
    _description = 'Petty Cash Create Payment'
    _check_company_auto = True

    date = fields.Date("Date", default=lambda self: fields.Date.context_today(self), required=True)
    company_id = fields.Many2one('res.company', string="Company", required=True)
    partner_id = fields.Many2one('res.partner', string="Expenses Partner")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    petty_cash_id = fields.Many2one('petty.cash.definition', string="Petty Cash")
    petty_cash_type = fields.Selection(string="Petty Cash Type", related='petty_cash_id.type')
    amount = fields.Monetary("Total Amount")
    journal_id = fields.Many2one('account.journal', string="Journal", company_dependent=True)
    payment_method_line_id = fields.Many2one('account.payment.method.line', string="Payment Method")
    payment_type = fields.Selection(
            [
                ('inbound', 'Inbound'),
                ('outbound', 'Outbound'),
            ], string="Payment Type", compute='_compute_payment_type'
    )
    sheet_ids = fields.Many2many('petty.cash.sheet', string="Sheets to Pay")
    origin = fields.Selection(
            [
                ('opening', 'Opening'),
                ('advance', 'Advance'),
                ('reposition', 'Reposition'),
                ('return', 'Return'),
                ('refund', 'Refund'),
            ], string="Origin"
    )
    # supplier_payment_form_id = fields.Many2one('account.payment.form', string="Payment Form")
    # payment_form_type = fields.Char(related='supplier_payment_form_id.type', string="Payment Form Type")
    ref = fields.Char("Ref")

    # @api.onchange('supplier_payment_form_id')
    # def _onchange_supplier_payment_form_id(self):
    #     self.journal_id = self.supplier_payment_form_id.journal_id.id
    #     self.ref = self.supplier_payment_form_id.name

    @api.depends('journal_id', 'origin')
    def _compute_payment_type(self):
        for rec in self:
            if rec.origin in ['advance', 'reposition', 'refund']:
                rec.payment_type = 'outbound'
            elif rec.origin == 'return':
                rec.payment_type = 'inbound'
            elif rec.origin == 'opening':
                rec.payment_type = 'outbound'

    @api.onchange('sheet_ids')
    def _onchange_sheet_ids(self):
        self.amount = 0
        if self.sheet_ids:
            for sheet in self.sheet_ids:
                self.amount += sheet.sheet_balance if sheet.petty_cash_type == 'reposition' else sheet.amount_total
                if not self.partner_id:
                    self.partner_id = sheet.expense_partner_id.id
            # self.origin = 'reposition'
        else:
            self.amount = 0
            # self.origin = 'advance'

    def create_payment(self):
        if not self.journal_id:
            msg = _("Journal is Required")
            raise UserError(msg)
        if not self.partner_id:
            msg = _("Expenses Partner Missing")
            raise UserError(msg)
        payment_ids = []
        if not self.sheet_ids:
            vals = {}
            if self.origin in ['advance', 'reposition', 'refund']:
                vals['payment_type'] = 'outbound'
            elif self.origin == 'return':
                vals['payment_type'] = 'inbound'
            elif self.origin == 'opening':
                vals['payment_type'] = 'outbound'
                vals['is_internal_transfer'] = True
                vals['destination_journal_id'] = self.petty_cash_id.petty_cash_journal_id.id
            vals['journal_id'] = self.journal_id.id
            vals['payment_method_line_id'] = self.payment_method_line_id.id
            vals['date'] = self.date
            vals['amount'] = self.amount
            vals['currency_id'] = self.currency_id.id
            vals['partner_id'] = self.partner_id.id
            vals['petty_cash_id'] = self.petty_cash_id.id
            vals['payment_origin'] = 'petty-cash'
            vals['memo'] = self.ref
            # vals['payment_form_id'] = self.supplier_payment_form_id.id
            if self.origin != 'opening':
                vals['petty_cash_destination_account_id'] = self.petty_cash_id.account_id.id

            payment = self.env['account.payment'].create(vals)
            if payment:
                # payment.action_post()
                payment_ids.append(payment.id)
        else:
            for sheet in self.sheet_ids:
                vals = {}
                if self.origin in ['advance', 'reposition', 'refund']:
                    vals['payment_type'] = 'outbound'
                elif self.origin == 'return':
                    vals['payment_type'] = 'inbound'
                vals['journal_id'] = self.journal_id.id
                vals['payment_method_line_id'] = self.payment_method_line_id.id
                vals['date'] = self.date
                vals['amount'] = abs(sheet.sheet_balance)
                vals['currency_id'] = self.currency_id.id
                vals['partner_id'] = self.partner_id.id
                vals['petty_cash_id'] = sheet.petty_cash_id.id
                vals['petty_cash_sheet_id'] = sheet.id
                vals['memo'] = self.ref
                vals['payment_origin'] = 'petty-cash'
                # vals['payment_form_id'] = self.supplier_payment_form_id.id
                vals['petty_cash_destination_account_id'] = self.petty_cash_id.account_id.id
                if self.journal_id.type == 'bank':
                    vals['payment_bank_id'] = self.journal_id.bank_id.id
                    ########################################################
                    # Check module not enabled at this point on this module
                    ########################################################

                    # if self.payment_method_line_id.check_type in ['check', 'deferred-check']
                    #     vals['issue_date'] = self.date
                    #     checkbook = self.env['account.checkbook'].search([('bank_id','=',self.journal_id.bank_id.id)])
                    #     if len(checkbook) == 1:
                    #         vals['checkbook_id'] = checkbook.id
                payment = self.env['account.payment'].create(vals)
                if payment:
                    # payment.action_post()
                    if self.origin == 'return':
                        sheet.write({
                            'return_payment_id'    : payment.id,
                            'return_payment_amount': payment.amount})
                    elif self.origin in ['advance', 'reposition', 'refund']:
                        sheet.write({
                            'refund_payment_id'    : payment.id,
                            'refund_payment_amount': payment.amount})
                    payment_ids.append(payment.id)

        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Petty Cash Payment'),
            'target'   : 'current',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'domain'   : [('id', 'in', payment_ids)]
        }
