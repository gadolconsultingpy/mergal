from odoo import api, models, fields, _
from odoo.exceptions import UserError


class PettyCashDefinition(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'petty.cash.definition'
    _description = 'Petty Cash Definition'
    _check_company_auto = True

    name = fields.Char("Name", required=True)
    type = fields.Selection(
            [
                ('fixed', 'Fixed Fund'),
                ('reposition', 'Expenses Reposition'),
                ('card', 'Expenses Card'),
            ], default='fixed',
    )
    opening_date = fields.Date("Opening Date", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    amount = fields.Monetary('Amount', copy=False)
    active = fields.Boolean('Active', default=True, tracking=True)
    owner_id = fields.Many2one('res.users', string="Owner", required=True, tracking=True)
    owner_partner_id = fields.Many2one('res.partner', string="Owner Partner", related='owner_id.partner_id')
    card_number = fields.Char("Card Number")
    journal_id = fields.Many2one('account.journal', string="Purchase Journal", tracking=True, company_dependent=True)
    petty_cash_journal_id = fields.Many2one('account.journal', string="Petty Cash Journal", tracking=True,
                                            company_dependent=True)
    account_id = fields.Many2one('account.account', string="Petty Cash Account", tracking=True, company_dependent=True)
    payment_ids = fields.One2many('account.payment', 'petty_cash_id', string="Payments",
                                  domain=[('petty_cash_sheet_id', '=', False)])
    payments_qty = fields.Integer('Payments Qty.', compute="_compute_payments_qty")
    sheet_ids = fields.One2many('petty.cash.sheet', 'petty_cash_id', string="Expenses Sheets",
                                domain=['|', ('state', 'in', ['draft', 'valid']), ('payment_state', 'in', ['unpaid'])])
    sheets_qty = fields.Integer("Sheets Qty.", compute="_compute_sheets_qty")
    payments_amount = fields.Monetary('Payments Amount', compute="_compute_payments_amount")
    expenses_amount = fields.Monetary('Expenses Amount', compute="_compute_expenses_amount")
    balance_amount = fields.Monetary('Balance', compute='_compute_balance_amount')
    progress = fields.Float("Progress", compute='_compute_progress')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id,
                                 required=True)
    fixed_fund_open = fields.Boolean("Fixed Fund Open", compute="_compute_fixed_fund_open")
    fixed_fund_open_manual = fields.Boolean('Fixed Fund Open Manually')
    has_sheet_to_replenish = fields.Boolean("Fixed Fund Reposition", compute="_compute_has_sheet_to_replenish")
    has_sheet_to_return = fields.Boolean("Has Sheets to Return", compute="_compute_sheets_to_retref")
    has_sheet_to_refund = fields.Boolean("Has Sheets to Refund", compute="_compute_sheets_to_retref")
    sheet_against_advance = fields.Boolean("Control Sheet against Advance", tracking=True)

    @api.onchange('petty_cash_journal_id')
    def _onchange_petty_cash_journal_id(self):
        self.account_id = self.petty_cash_journal_id.default_account_id.id

    @api.depends('sheet_ids')
    def _compute_sheets_to_retref(self):
        for rec in self:
            if rec.type == 'reposition':
                rec.has_sheet_to_return = len([x for x in rec.sheet_ids if x.sheet_balance > 0])
                rec.has_sheet_to_refund = len([x for x in rec.sheet_ids if x.sheet_balance < 0])
            else:
                rec.has_sheet_to_return = False
                rec.has_sheet_to_refund = False

    @api.depends('balance_amount')
    def _compute_progress(self):
        for record in self:
            try:
                if record.type == 'fixed':
                    record.progress = 100 - int(record.balance_amount * 100 / record.amount or record.balance_amount)
                else:
                    record.progress = 100 - int(record.balance_amount * 100 / record.payments_amount or
                                                record.balance_amount)
            except BaseException as errstr:
                record.progress = 0

    @api.depends('sheet_ids')
    def _compute_expenses_amount(self):
        for record in self:
            record.expenses_amount = 0
            for sheet in record.sheet_ids.filtered(lambda x: x.payment_state == 'unpaid'):
                if sheet.petty_cash_type == 'reposition':
                    record.expenses_amount -= sheet.sheet_balance
                else:
                    record.expenses_amount -= sheet.amount_total

    @api.depends('payment_ids')
    def _compute_payments_amount(self):
        for record in self:
            record.payments_amount = 0
            for payment in record.payment_ids:
                if payment.payment_type == 'outbound':
                    record.payments_amount += payment.amount
                elif payment.payment_type == 'inbound':
                    record.payments_amount -= payment.amount

    @api.depends('sheet_ids')
    def _compute_balance_amount(self):
        for record in self:
            if record.type == 'reposition':
                record.balance_amount = record.payments_amount + record.expenses_amount
            else:
                record.balance_amount = record.amount + record.expenses_amount

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'reposition':
            self.amount = False
            self.currency_id = self.env.company.currency_id.id

    @api.depends('payment_ids')
    def _compute_payments_qty(self):
        for record in self:
            payments = record.env['account.payment'].search_count(
                    [
                        ('petty_cash_id', '=', record.id),
                    ]
            )
            record.payments_qty = payments

    @api.depends('sheet_ids')
    def _compute_sheets_qty(self):
        for record in self:
            sheets = record.env['petty.cash.sheet'].search_count(
                    [
                        ('petty_cash_id', '=', record.id),
                    ]
            )
            record.sheets_qty = sheets

    @api.depends('payment_ids')
    def _compute_fixed_fund_open(self):
        for rec in self:
            if rec.type == 'fixed':
                if rec.fixed_fund_open_manual:
                    rec.fixed_fund_open = True
                else:
                    rec.fixed_fund_open = len(
                        rec.payment_ids.filtered(lambda s: s.payment_type == 'outbound' and s.state
                                                           == 'posted')) > 0
            else:
                rec.fixed_fund_open = False

    @api.depends('sheet_ids')
    def _compute_has_sheet_to_replenish(self):
        for rec in self:
            sheet_to_replenish = rec.sheet_ids.filtered(lambda s: s.state == 'confirm' and s.payment_state == 'unpaid')
            rec.has_sheet_to_replenish = len(sheet_to_replenish) > 0

    def open_payments(self):
        moves = self.env['account.payment'].search(
                [
                    ('petty_cash_id', '=', self.id),
                ]
        )
        if moves:
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Payments'),
                'target'   : 'current',
                'view_mode': 'list,form',
                'res_model': 'account.payment',
                'domain'   : [('id', 'in', [x.id for x in moves])]
            }

    def open_sheets(self):
        moves = self.env['petty.cash.sheet'].search(
                [
                    ('petty_cash_id', '=', self.id),
                ]
        )
        if moves:
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Sheets'),
                'target'   : 'current',
                'view_mode': 'list,form',
                'res_model': 'petty.cash.sheet',
                'domain'   : [('id', 'in', [x.id for x in moves])]
            }

    def generate_sheet(self):
        sheet = self.env['petty.cash.sheet'].create(
                {
                    'company_id'        : self.company_id.id,
                    'petty_cash_id'     : self.id,
                    'owner_partner_id'  : self.owner_id,
                    'user_id'           : self.env.user.id,
                    'expense_partner_id': self.owner_id.partner_id.id if self.type == 'fixed' else False,
                }
        )
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Petty Cash Sheet'),
            'target'   : 'current',
            'view_mode': 'form',
            'res_model': 'petty.cash.sheet',
            'res_id'   : sheet.id
        }

    def get_petty_cash_definition(self):
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Petty Cash Definition'),
            'res_model': 'petty.cash.definition',
            'view_mode': 'form',
            'target'   : 'current',
            'res_id'   : self.id,
        }

    # Advance Payments
    def generate_opening_payment(self):
        if self.type != 'fixed':
            msg = _("Only for Fixed Funds")
            raise UserError(msg)
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'opening'
        vals['partner_id'] = self.owner_partner_id.id
        vals['amount'] = self.amount
        wizard = self.env['petty.cash.create.payment'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }

    def generate_advance(self):
        if self.type != 'reposition':
            msg = _("Only for Reposition Funds")
            raise UserError(msg)
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'advance'
        wizard = self.env['petty.cash.create.payment'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }

    def generate_advance_2(self):  # deprecated
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'advance'
        if self.type in ['fixed', 'card']:
            vals['partner_id'] = self.owner_partner_id.id
        sheet_ids = self.sheet_ids.filtered(lambda s: s.state == 'confirm' and s.payment_state == 'unpaid')
        if self.type == 'fixed':
            vals['sheet_ids'] = sheet_ids
            vals['amount'] = sum(sheet_ids.mapped('amount_total'))
        elif self.type == 'reposition':
            vals['partner_id'] = None
            sheet_ids = sheet_ids.filtered(lambda s: s.sheet_balance < 0)
            vals['sheet_ids'] = sheet_ids
            vals['amount'] = abs(sum(sheet_ids.mapped('sheet_balance')))
            for sheet in sheet_ids:
                if not vals['partner_id']:
                    vals['partner_id'] = sheet.expense_partner_id.id

        wizard = self.env['petty.cash.create.payment'].create(vals)
        if self.type == 'fixed':
            if vals['sheet_ids']:
                wizard._onchange_sheet_ids()
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }

    # Reposition (fixed)
    def generate_replenishment(self):
        if self.type != 'fixed':
            msg = _("Only for Fixed Funds")
            raise UserError(msg)
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'reposition'
        vals['partner_id'] = self.owner_partner_id.id
        sheet_to_replenish = self.sheet_ids.filtered(lambda s: s.state == 'confirm' and s.payment_state == 'unpaid')
        if not sheet_to_replenish:
            msg = _("There Is No Confirmed Sheets to Replenish")
            raise UserError(msg)
        vals['sheet_ids'] = sheet_to_replenish
        vals['amount'] = sum(sheet_to_replenish.mapped('amount_total'))
        wizard = self.env['petty.cash.create.payment'].create(vals)
        wizard._onchange_sheet_ids()
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }

    # Return Payment
    def generate_return_payment(self):
        if self.type != 'reposition':
            msg = _("Only for Repositio Funds")
            raise UserError(msg)
        # return means: received from employee as payment not realized
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'return'
        vals['partner_id'] = False
        amount = 0
        sheet_ids = self.sheet_ids.filtered(lambda s: s.state == 'confirm' and s.payment_state == 'unpaid')
        sheet_ids = sheet_ids.filtered(lambda s: s.sheet_balance > 0)
        vals['sheet_ids'] = sheet_ids.mapped('id')
        for sheet in sheet_ids:
            amount += sheet.sheet_balance
            if not vals['partner_id']:
                vals['partner_id'] = sheet.expense_partner_id.id
            vals['amount'] = sheet.sheet_balance
        wizard = self.env['petty.cash.create.payment'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Return Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }

    # Refund Payment
    def generate_refund_payment(self):
        if self.type != 'reposition':
            raise UserError("Only for Repositio Funds")
        # return means: payment to employee because expenses realized exceeded the advance
        vals = {}
        vals['company_id'] = self.company_id.id
        vals['currency_id'] = self.currency_id.id
        vals['petty_cash_id'] = self.id
        vals['origin'] = 'refund'
        vals['partner_id'] = False
        sheet_ids = self.sheet_ids.filtered(lambda s: s.state == 'confirm' and s.payment_state == 'unpaid')
        sheet_ids = sheet_ids.filtered(lambda s: s.sheet_balance < 0)
        vals['sheet_ids'] = sheet_ids.mapped('id')
        vals['amount'] = 0
        for sheet in sheet_ids:
            if not vals['partner_id']:
                vals['partner_id'] = sheet.expense_partner_id.id
            vals['amount'] += abs(sheet.sheet_balance)
        wizard = self.env['petty.cash.create.payment'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Create Return Payment'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.create.payment',
            'res_id'   : wizard.id
        }
