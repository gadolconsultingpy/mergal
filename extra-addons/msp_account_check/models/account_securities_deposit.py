import datetime
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountSecuritiesDeposit(models.Model):
    _name = 'account.securities.deposit'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _description = 'Securities Deposit'
    _order = 'date desc,id desc'
    _check_company_auto = True

    name = fields.Char("Name")
    date = fields.Date("Date", default=lambda self: fields.Date.context_today(self), required=True)
    value_date = fields.Date("Value Date", default=lambda self: datetime.datetime.now().date())
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    bank_id = fields.Many2one('res.bank', string="Bank")
    bank_journal_id = fields.Many2one('account.journal', string="Bank Journal", company_dependent=True)
    payment_method_line_id = fields.Many2one('account.payment.method.line', string="Payment Method Line")
    number = fields.Char("Deposit Number", required=True)
    check_ids = fields.One2many('account.securities.deposit.line', 'parent_id')
    cash_amount = fields.Monetary('Cash Amount')
    total_amount = fields.Monetary('Deposit Total', compute='_compute_total_amount')
    state = fields.Selection(
            [
                ('draft', 'Draft'),
                ('confirm', 'Confirmed'),
                ('done', 'Done'),
            ], string="State", default='draft'
    )
    state_ro = fields.Selection(string="State (ro)", related='state')
    # branch_id = fields.Many2one('res.branch', string="Branch", required=True,
    #                             default=lambda self: self.env.user.branch_id.id)
    account_move_qty = fields.Integer("Account Moves", compute="_compute_account_move_qty")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)

    def _compute_account_move_qty(self):
        for rec in self:
            moves = self.env['account.move'].search([('deposit_id', '=', rec.id)])
            rec.account_move_qty = len(moves)

    @api.depends('check_ids')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum([x.amount for x in rec.check_ids]) + rec.cash_amount

    def action_confirm(self):
        self.state = 'confirm'

    def action_validate(self):
        # VALIDATE CHECK STATE
        for line in self.check_ids:
            if line.check_id.state != 'in-portfolio':
                msg = "Cheque No Está En Cartera: %s, %s" % (line.check_id.bank_id.name, line.check_id.number)
                raise UserError(msg)
            else:
                line.check_id.state = "deposited"
        self.create_account_move()
        # self.create_account_move_bank()
        self.state = 'done'

    def action_reset_to_draft(self):
        if self.state != 'done':
            return
        for check in self.check_ids:
            if check.check_id.state != 'deposited':
                msg = "Cheque No Está en Estado Depositado: %s, %s" % (
                    check.check_id.bank_id.name, check.check_id.number)
                raise UserError(msg)
            else:
                check.check_id.state = 'in-portfolio'
        moves = self.env['account.move'].search([('deposit_id', '=', self.id)])
        for move in moves:
            print(move.id)
            move.button_draft()
            move.name = ""
            move.unlink()
        self.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountSecuritiesDeposit, self).create(vals_list)
        for record in records:
            sequence_code = "account.securities.deposit"
            sequence = record.env['ir.sequence'].search([
                ('code', '=', sequence_code),
                ('company_id', '=', record.company_id.id or record.env.company.id)
            ])
            if not sequence:
                raise UserError(_("Sequence Not Found: %s" % sequence_code))
            record.name = sequence.next_by_code(sequence_code)
        return records

    @api.onchange('bank_journal_id')
    def _onchange_bank_journal_id(self):
        self.bank_id = self.bank_journal_id.bank_id.id

    def create_account_move(self):
        vals = self.prepare_account_move_values()
        move = self.env['account.move'].create(vals)
        if move:
            move.action_post()
        else:
            raise UserError("Error Creating Account Move")

    # def create_account_move_bank(self):
    #     vals = self.prepare_account_move_bank_values()
    #     move = self.env['account.move'].create(vals)
    #     if move:
    #         move.action_post()
    #     else:
    #         raise UserError("Error Creating Account Move")

    def reconcile_deposit(self, move):
        vals = {}
        vals['name'] = self.name
        vals['journal_id'] = move.journal_id.id
        vals['date'] = self.date
        vals['deposit_id'] = self.id

        line_ids = []
        ivals = {}
        ivals['date'] = self.date
        ivals['payment_ref'] = self.number
        ivals['partner_id'] = self.env.company.partner_id.id
        ivals['amount'] = self.total_amount
        line_ids.append((0, 0, ivals))

        vals['line_ids'] = line_ids
        statement = self.env['account.bank.statement'].create(vals)
        statement.write({'balance_end_real': statement.balance_end})
        _logger.info("Bank Statement created: (%s), %s" % (statement.id, statement.name))
        _logger.info("Posting")
        statement.button_post()
        _logger.info("Reconciling")
        idx = 0
        for lines in statement.line_ids:
            idx += 1
            # print("res = lines.reconcile([])")
            # lines.write({'partner_id':False})
            lines.reconcile_py([], check_open_balance=False)
        try:
            _logger.info("Validating")
            statement.button_validate_or_action()
        except BaseException as errstr:
            _logger.error(errstr)

    def prepare_account_move_values(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        vals = {}
        vals['ref'] = self.number
        vals['journal_id'] = self.bank_journal_id.id
        vals['date'] = self.value_date
        # vals['branch_id'] = self.branch_id.id
        vals['deposit_id'] = self.id

        lines = []
        dvals = {}
        # Outstanding Receipts Account
        # dvals['account_id'] = self.env.company.account_journal_payment_debit_account_id.id
        # Bank Account
        dvals['account_id'] = self.payment_method_line_id.payment_account_id.id
        #####

        dvals['partner_id'] = self.env.company.partner_id.id
        dvals['name'] = self.number
        dvals['debit'] = self.total_amount
        lines.append((0, 0, dvals))
        for check in self.check_ids:
            cvals = {}
            cvals['account_id'] = check.check_id.payment_method_line_id.payment_account_id.id
            cvals['partner_id'] = check.partner_id.id
            cvals['name'] = check.check_id.name
            cvals['credit'] = check.amount
            lines.append((0, 0, cvals))
        if self.cash_amount:
            cvals = {}
            cvals['account_id'] = config.cash_account_id.id
            cvals['name'] = config.cash_account_id.name
            cvals['credit'] = self.cash_amount
            lines.append((0, 0, cvals))

        vals['line_ids'] = lines
        return vals

    def prepare_account_move_bank_values(self):
        vals = {}
        vals['ref'] = self.name
        vals['journal_id'] = self.bank_journal_id.id
        vals['date'] = self.value_date
        # vals['branch_id'] = self.branch_id.id
        vals['deposit_id'] = self.id

        lines = []
        dvals = {}
        dvals['account_id'] = self.bank_journal_id.default_account_id.id
        # dvals['partner_id'] = self.env.company.partner_id.id
        dvals['name'] = self.number
        dvals['debit'] = self.total_amount
        lines.append((0, 0, dvals))

        cvals = {}
        cvals['account_id'] = self.bank_journal_id.suspense_account_id.id
        # dvals['partner_id'] = self.env.company.partner_id.id
        cvals['name'] = self.number
        cvals['credit'] = self.total_amount
        lines.append((0, 0, cvals))

        vals['line_ids'] = lines
        return vals

    def open_account_move(self):
        moves = self.env['account.move'].search(
                [
                    ('deposit_id', '=', self.id)
                ]
        )
        if moves:
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Account Moves'),
                'target'   : 'current',
                'view_mode': 'list,form',
                'res_model': 'account.move',
                'domain'   : [('id', 'in', [x.id for x in moves])]
            }

    def open_bank_statement(self):
        statement = self.env['account.bank.statement'].search(
                [
                    ('deposit_id', '=', self.id)
                ]
        )
        if statement:
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Bank Statement'),
                'target'   : 'current',
                'view_mode': 'form',
                'res_model': 'account.bank.statement',
                'res_id'   : statement.id
            }

    @api.model
    def _create_sequences(self):
        template_company = self.env.ref('base.main_company')
        template_sequence = self.env['ir.sequence'].search(
                [
                    ('code', '=', 'account.securities.deposit'),
                    ('company_id', '=', template_company.id)
                ]
        )
        companies = self.env['res.company'].search(
                [
                    ('id', '!=', template_company.id)
                ]
        )
        for comp in companies:
            defs = {}
            defs['company_id'] = comp.id
            template_sequence.copy(default=defs)
        # pass


class AccountSecuritiesDepositLine(models.Model):
    _name = 'account.securities.deposit.line'
    _description = 'Securities Deposit Line'

    parent_id = fields.Many2one('account.securities.deposit', string="Deposit", ondelete="cascade")
    parent_company_id = fields.Many2one(related='parent_id.company_id')
    check_id = fields.Many2one('account.check', string="Check")
    check_date = fields.Date('Date', related='check_id.issue_date')
    check_exp_date = fields.Date('Accr. Date', related='check_id.accreditation_date')
    partner_id = fields.Many2one('res.partner', string="Partner", related='check_id.partner_id')
    currency_id = fields.Many2one('res.currency', string="Currency", related='parent_id.currency_id')
    amount = fields.Monetary("Amount", related='check_id.amount')
    number = fields.Char('Number', related='check_id.number')
