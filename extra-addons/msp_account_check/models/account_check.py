import datetime
from odoo.osv import expression

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountCheck(models.Model):
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _name = "account.check"
    _description = "Checks"
    _check_company_auto = True

    name = fields.Char(string="Check number", copy=False)
    issue_date = fields.Date(string="Issue Date", required=True, default=lambda self: datetime.datetime.now())
    accreditation_date = fields.Date(string="Accreditation Date", required=True, tracking=True,
                                     default=lambda self: datetime.datetime.now())
    accreditation_days = fields.Integer("days", compute="_compute_accreditation_days", store=True, tracking=True)
    accreditation_status = fields.Boolean("Accredited", compute="_compute_accreditation_status")
    partner_id = fields.Many2one('res.partner', string="Issuer", tracking=True)
    issuer_name = fields.Char(string="Issuer Name", required=True, tracking=True)
    number = fields.Char('Number', tracking=True)
    amount = fields.Monetary(string="Amount", required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True,
                                  default=lambda self: self.env.company.currency_id.id, tracking=True)
    reference = fields.Char(string="Reference")
    endorsed = fields.Boolean(string="Endorsed", tracking=True)
    non_negotiable = fields.Boolean(string="Non-Negotiable", tracking=True)
    state = fields.Selection(string="State", selection=[
        ('draft', 'Draft'),
        ('in-portfolio', 'In Portfolio'),
        ('issued', 'Issued'),
        ('credited', 'Credited'),
        ('deposited', 'Deposited'),
        ('rejected', 'Rejected'),
        ('replace', 'Replaced'),
        ('cancel', 'Cancelled'),
    ], default="draft", tracking=True)
    state_ro = fields.Selection(string="State (ro)", related='state', tracking=True)
    state_own_ro = fields.Selection(string="State Own (ro)", related='state', tracking=True)
    type = fields.Selection(string="Type", selection=[
        ('own', 'Own'),
        ('third', 'Third')
    ], default="third")
    check_type = fields.Selection(
            [
                ('check', "Check"),
                ('post-dated', "Deferred Check"),
            ], default='check', string="Check Type", compute="_compute_check_type", store=True
    )
    bank_id = fields.Many2one('res.bank', string="Issuer Bank", required=True)
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account")
    # branch_id = fields.Many2one('res.branch', string="Branch", default=lambda self: self.env.user.branch_id.id)
    payee = fields.Char(string="Pay to the Order of", tracking=True,
                        help="Name written on the check")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id,
                                 readonly=True)
    journal_id = fields.Many2one('account.journal', string="Journal",
                                 company_dependent=True,
                                 help='Journal in which check is first entered')
    deposits_qty = fields.Integer('Deposits Qty.', compute='_compute_deposits_qty')
    move_ids = fields.One2many('account.move', 'check_id', string="Account Moves")
    move_qty = fields.Integer("Account Moves Qty.", compute="_compute_move_qty")
    rejected_before = fields.Boolean("Rejected Before", default=False, copy=False)
    checkbook_id = fields.Many2one('account.checkbook', string="Checkbook", ondelete='restrict',
                                   company_dependent=True, )
    preview_number = fields.Char("Preview Number")
    bearer_check = fields.Boolean("Bearer Check")
    payment_method_line_id = fields.Many2one('account.payment.method.line', string="Payment Method Line")

    @api.constrains('issue_date', 'accreditation_date')
    def _constraint_dates_control(self):
        if self.accreditation_date < self.issue_date:
            raise UserError(_("The accreditation date cannot be prior to the issue"))

    @api.onchange('bearer_check')
    def _onchange_bearer_check(self):
        if self.bearer_check:
            self.payee = ""

    @api.onchange('checkbook_id')
    def _onchange_checkbook_id(self):
        self.bank_id = self.checkbook_id.bank_id.id
        self.bank_account_id = self.checkbook_id.bank_account_id.id
        self.journal_id = self.checkbook_id.journal_id.id
        self.check_type = self.checkbook_id.check_type

    def default_get(self, fields_list):
        vals = super(AccountCheck, self).default_get(fields_list)
        if vals.get('type') == 'own':
            vals['partner_id'] = self.env.company.partner_id.id
        elif vals.get('type') == 'third':
            vals['payee'] = self.env.company.partner_id.name
        return vals

    def open_account_moves(self):
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Account Moves'),
            'target'   : 'current',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain'   : [('id', 'in', [x.id for x in self.move_ids])]
        }

    @api.depends('move_ids')
    def _compute_move_qty(self):
        for rec in self:
            rec.move_qty = len(rec.move_ids)

    def open_deposits(self):
        deposits = self.env['account.securities.deposit.line'].search(
                [
                    ('check_id', '=', self.id)
                ]
        )
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Securities Deposit'),
            'target'   : 'current',
            'view_mode': 'list,form',
            'res_model': 'account.securities.deposit',
            'domain'   : [('id', 'in', [x.parent_id.id for x in deposits if x.parent_id])]
        }

    def _compute_deposits_qty(self):
        for rec in self:
            deposits = self.env['account.securities.deposit.line'].with_context(prefetch_fields=False).search(
                    [
                        ('check_id', '=', rec.id)
                    ]
            )
            rec.deposits_qty = len(deposits)

    @api.depends('issue_date', 'accreditation_date', 'checkbook_id')
    def _compute_check_type(self):
        for rec in self:
            rec.check_type = 'check'
            if rec.checkbook_id:
                rec.check_type = rec.checkbook_id.check_type
            else:
                if rec.issue_date != rec.accreditation_date:
                    rec.check_type = 'post-dated'

    # @api.onchange('issue_date','accreditation_date')
    # def _onchange_check_type(self):
    #     self.check_type = 'check'
    #     if self.issue_date != self.accreditation_date:
    #         self.check_type = 'post-dated'

    @api.model
    def batch_deposit(self):
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids') or self.env.context.get('active_id')
        checks = self.env[active_model].browse(active_ids).filtered(lambda x: x.state == 'in-portfolio').mapped('id')

        vals = {}
        vals['check_ids'] = [(0, 0, {'check_id': x}) for x in checks]
        deposit = self.env['account.securities.deposit'].create(vals)
        # if deposit:
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Securities Deposit'),
            'target'   : 'current',
            'view_mode': 'form',
            'res_model': 'account.securities.deposit',
            'res_id'   : deposit.id
        }
        # else:
        #     raise UserError("Error Creating Deposit: %s" % (deposit))

    @api.model
    def format_value(self, value):
        return "{:,.0f}".format(value).replace(",", ":").replace(".", ",").replace(":", ".")

    def name_get(self):
        names = []
        for rec in self:
            names.append([rec.id, "%s, %s, %s %s " % (
                rec.bank_id.name, rec.number or "id %s" % (rec.id), rec.format_value(rec.amount),
                rec.currency_id.symbol)])
        return names

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order=""):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        # To search records based on Field name, Field technical name, Model name and Model technical name
        else:
            domain = ['|', ('name', operator, name), ('number', "=", name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.depends('issue_date', 'accreditation_date')
    def _compute_accreditation_days(self):
        for rec in self:
            rec.accreditation_days = (rec.accreditation_date - rec.issue_date).days

    @api.depends('accreditation_date')
    def _compute_accreditation_status(self):
        for rec in self:
            if datetime.date.today() > rec.accreditation_date:
                rec.accreditation_status = True
            else:
                rec.accreditation_status = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountCheck, self).create(vals_list)
        for record in records:
            check_type = record.type
            sequence_code = "account.check.%s" % (check_type)
            sequence = record.env['ir.sequence'].search(
                    [
                        ('code', '=', sequence_code),
                        ('company_id', '=', record.company_id.id)
                    ]
            )
            if not sequence:
                msg = _("Sequence Not Found: {}")
                raise UserError(msg.format(sequence_code))
            record.name = sequence.next_by_code(sequence_code)
            # if record.payee:
            #     record.payee = record.env.company.name
        return records

    def set_number(self):
        if not self.name:
            sequence_code = "account.check.%s" % (self.type)
            sequence = self.env['ir.sequence'].search(
                    [
                        ('code', '=', sequence_code),
                        ('company_id', '=', self.company_id.id)
                    ]
            )
            if not sequence:
                msg = _("Sequence Not Found: {}")
                raise UserError(msg.format(sequence_code))
            self.name = sequence.next_by_code(sequence_code)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.issuer_name:
            self.issuer_name = self.partner_id.name if self.partner_id else ''

    def action_reject(self):
        if self.state != 'deposited':
            msg = _("Check Was Not Deposited. State: {}")
            raise UserError(msg.format(self.state))
        self.create_rejected_account_move()
        self.state = "rejected"
        self.rejected_before = True

    def action_cancel(self):
        if self.state != 'issued':
            msg = _("Check Was Not Issued State. State: {}")
            raise UserError(msg.format(self.state))
        self.state = 'cancel'

    def create_rejected_account_move(self):
        vals = self.prepare_rejected_account_move_values()
        move = self.env['account.move'].create(vals)
        if move:
            move.action_post()
        else:
            raise UserError(_("Error Creating Account Move"))

    def action_return_to_portfolio(self):
        if self.state != 'rejected':
            msg = _("Check Can Not Return to Portfolio. State: {}")
            raise UserError(msg.format(self.state))
        self.create_portfolio_account_move()
        self.state = "in-portfolio"

    def create_portfolio_account_move(self):
        vals = self.prepare_portfolio_account_move_values()
        move = self.env['account.move'].create(vals)
        if move:
            move.action_post()
        else:
            raise UserError(_("Error Creating Account Move"))

    def action_draft(self):
        if self.state != 'in-portfolio':
            msg = _('Check Can Not Be Changed to Draft. State: {}')
            raise UserError(msg.format(self.state))
        self.state = 'draft'

    def action_portfolio(self):
        if self.state != 'draft':
            msg = _('Check Can Not Be Received in Portfolio. State: {}')
            raise UserError(msg.format(self.state))
        self.state = 'in-portfolio'

    def prepare_rejected_account_move_values(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        last_deposit = self.env['account.securities.deposit.line'].search(
                [
                    ('check_id', '=', self.id)
                ], order="id desc", limit=1
        )
        if not last_deposit:
            raise UserError(_('Can Not Find Last Deposit'))
        last_deposit = last_deposit.parent_id
        vals = {}
        vals['ref'] = self.name
        vals['journal_id'] = config.rejected_journal_id.id
        vals['date'] = fields.Date.context_today(self)
        # vals['branch_id'] = self.branch_id.id
        vals['check_id'] = self.id

        lines = []
        dvals = {}
        dvals['account_id'] = config.rejected_journal_id.default_account_id.id
        # self.bank_journal_id.suspense_account_id.id
        dvals['name'] = self.name
        dvals['debit'] = self.amount
        lines.append((0, 0, dvals))

        cvals = {}
        cvals['account_id'] = last_deposit.bank_journal_id.default_account_id.id
        cvals['partner_id'] = self.partner_id.id
        cvals['name'] = last_deposit.name
        cvals['credit'] = self.amount
        lines.append((0, 0, cvals))

        vals['line_ids'] = lines
        return vals

    def prepare_portfolio_account_move_values(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        vals = {}
        vals['ref'] = self.name
        vals['journal_id'] = config.in_portfolio_journal_id.id
        vals['date'] = fields.Date.context_today(self)
        # vals['branch_id'] = self.branch_id.id
        vals['check_id'] = self.id

        lines = []
        dvals = {}
        dvals['account_id'] = config.in_portfolio_journal_id.default_account_id.id
        dvals['partner_id'] = self.partner_id.id
        dvals['name'] = self.name
        dvals['debit'] = self.amount
        lines.append((0, 0, dvals))

        cvals = {}
        cvals['account_id'] = config.rejected_journal_id.default_account_id.id
        cvals['partner_id'] = self.partner_id.id
        dvals['name'] = self.name
        cvals['credit'] = self.amount
        lines.append((0, 0, cvals))

        vals['line_ids'] = lines
        return vals

    @api.model
    def _create_third_sequences(self):
        template_company = self.env.ref('base.main_company')
        template_sequence = self.env['ir.sequence'].search(
                [
                    ('code', '=', 'account.check.third'),
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

    @api.model
    def _create_own_sequences(self):
        template_company = self.env.ref('base.main_company')
        template_sequence = self.env['ir.sequence'].search(
                [
                    ('code', '=', 'account.check.own'),
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
