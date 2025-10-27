from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PettyCashSheet(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'petty.cash.sheet'
    _description = 'Expenses Sheet'
    _order = "date desc, name desc"
    _check_company_auto = True

    name = fields.Char("Name")
    date = fields.Date("Date", default=lambda self: fields.Date.context_today(self))
    petty_cash_id = fields.Many2one('petty.cash.definition', string="Petty Cash", ondelete='restrict')
    # TODO: readonly=True, states={'draft': [('readonly', False)]}, )
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    # TODO:  readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('petty.cash.sheet.line', 'sheet_id', string="Expenses Detail")
    amount_total = fields.Monetary('Expenses Total', compute="_compute_amount_total", store=True)
    state = fields.Selection(
            [
                ('draft', 'Draft'),
                ('valid', 'Validated'),
                ('confirm', 'Confirmed'),
            ], default='draft', string="State", tracking=True
    )
    payment_state = fields.Selection(
            [
                ('unpaid', 'Unpaid'),
                ('paid', 'Paid'),
            ], default='unpaid', string="Payment State", tracking=True
    )
    comment = fields.Text('Comment')
    expense_partner_id = fields.Many2one('res.partner', string='Expenses Contact', tracking=True)
    # TODO: readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id,
                                 readonly=True)
    invoice_ids = fields.One2many('account.move', 'petty_cash_sheet_id', string="Invoices",
                                  domain=[('move_type', '=', 'in_invoice')])
    invoices_qty = fields.Integer('Invoices Qty.', compute="_compute_invoices_qty")
    account_move_ids = fields.One2many('account.move', 'petty_cash_sheet_id', string="Account Moves",
                                       domain=[('move_type', '=', 'entry')])
    account_moves_qty = fields.Integer("Account Moves Qty.", compute="_compute_account_moves_qty")
    user_id = fields.Many2one('res.users', string="User", readonly=True)
    owner_partner_id = fields.Many2one('res.partner', string="Responsible", related='user_id.partner_id')
    petty_cash_type = fields.Selection(related='petty_cash_id.type', string="Petty Cash Type")
    # Advance payment for Repositions
    advance_payment_id = fields.Many2one('account.payment', string="Advance Payment", tracking=True)
    advance_payment_amount = fields.Monetary('Payment Amount', related='advance_payment_id.amount')
    # Return payment when cash returned
    return_payment_id = fields.Many2one('account.payment', string="Return Payment", tracking=True)
    return_payment_amount = fields.Monetary("Return Amount", related='return_payment_id.amount')
    # Refund Payment when expense exceeds the advance
    refund_payment_id = fields.Many2one('account.payment', string="Refund Payment", tracking=True)
    refund_payment_amount = fields.Monetary('Refund Amount', related='refund_payment_id.amount')
    #
    # payment_balance_amount = fields.Monetary("Payment Balance", compute="_compute_payment_balance_amount")
    sheet_against_advance = fields.Boolean('Sheet against Advance', related='petty_cash_id.sheet_against_advance')
    sheet_balance = fields.Monetary('Sheet Balance', help="Fixed Fund: The Balance is the amount to be replenished, "
                                                          "Reposition: The Balance is the amount to be returned or "
                                                          "refunded",
                                    compute="_compute_sheet_balance")

    @api.model_create_multi
    def create(self, vals):
        records = super(PettyCashSheet, self).create(vals)
        for record in records:
            sequence_code = record._name
            sequence = record.env['ir.sequence'].search(
                    [
                        ('code', '=', sequence_code),
                        ('company_id', '=', record.company_id.id)
                    ]
            )
            if not sequence:
                msg = _("Sequence Not Found")
                raise UserError(f"{msg}: {sequence_code}")
            record.name = sequence.next_by_code(sequence_code)
        return records

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                msg = _("You Cannot Delete Records That Are Not in Draft")
                raise UserError(msg)
        return super(PettyCashSheet, self).unlink()

    @api.depends("line_ids")
    def _compute_invoices_qty(self):
        for record in self:
            record.invoices_qty = len(record.invoice_ids)

    @api.depends("account_move_ids")
    def _compute_account_moves_qty(self):
        for record in self:
            record.account_moves_qty = len(record.account_move_ids)

    @api.depends('line_ids')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum([x.price_total for x in record.line_ids])

    # @api.depends('advance_payment_id', 'amount_total')
    # def _compute_payment_balance_amount(self):
    #     for rec in self:
    #         if rec.advance_payment_id:
    #             rec.payment_balance_amount = rec.advance_payment_id.amount - rec.amount_total - rec.return_payment_amount
    #         else:
    #             rec.payment_balance_amount = 0

    @api.depends('advance_payment_id', 'return_payment_id', 'refund_payment_id')
    def _compute_sheet_balance(self):
        for rec in self:
            rec.sheet_balance = rec.advance_payment_amount - rec.return_payment_amount
            rec.sheet_balance += -rec.amount_total + rec.refund_payment_amount

    def action_draft(self):
        for move in self.account_move_ids:
            move.button_draft()
            move.write({'posted_before': False})
            move.unlink()
        if self.advance_payment_id:
            self.advance_payment_id.write({'petty_cash_sheet_id': False})
        self.state = 'draft'
        self.payment_state = 'unpaid'

    def action_valid(self):
        if self.petty_cash_type == 'reposition':
            if self.sheet_against_advance and not self.advance_payment_id:
                msg = _("Advance Payment Missing")
                raise UserError(msg)
            if self.advance_payment_id and self.advance_payment_id.petty_cash_sheet_id:
                msg = _("The Advance Has Already Reconciled")
                raise UserError(msg)
        if not self.line_ids or sum([x.price_total for x in self.line_ids]) == 0:
            msg = _("The Petty Cash Has No Detail")
            raise UserError(msg)
        for idx, line in enumerate(self.line_ids, start=1):
            if not line.price_total:
                msg = _("The Total Cannot Be Zero: Line %s") % (idx)
                raise UserError(msg)
            if line.concept_id.require_invoice:
                if not line.account_move_id:
                    msg = _("The Line Require an Invoice: %s - %s") % (line.concept_id.name, line.date)
                    raise UserError(msg)
                if line.account_move_id.state != 'posted':
                    msg = _("Invoice not Confirmed: %s") % (line.account_move_id.display_name)
                    raise UserError(msg)
            else:
                if not line.account_id:
                    msg = _("Missing Account: Line %s") % (idx)
                    raise UserError(msg)
                if line.account_move_id:
                    msg = _("The Line Does Not Require an Invoice: %s - %s") % (line.concept_id.name, line.date)
                    raise UserError(msg)
        self.amount_total = sum([x.price_total for x in self.line_ids])
        if self.petty_cash_id.type == 'fixed' and self.petty_cash_id.balance_amount < 0:
            msg = _("The Petty Cash Does Not Have Enough Fund for this Sheet")
            raise UserError(msg)
        self.state = 'valid'

    def action_confirm(self):
        for line in self.line_ids:
            if line.concept_id.require_invoice:
                # line._onchange_account_move_id()
                if line.account_move_id.state != 'posted':
                    msg = _("The Invoice Is Not Posted")
                    raise UserError(msg)
        # Contabilización FACTURAS
        move = self.create_invoice_payments_move()
        self.reconcile_invoices_payments(move)
        # Contabilización CONCEPTOS
        self.create_concepts_move()

        if self.petty_cash_type == 'reposition' and self.advance_payment_id:
            if self.sheet_balance == 0:
                self.payment_state = 'paid'
            self.advance_payment_id.write({'petty_cash_sheet_id': self.id})
        self.state = "confirm"

    def action_print(self):
        document = self.env.ref('msp_petty_cash.petty_cash_sheet_report_action').report_action(self, data={})
        return document

    def create_concepts_move(self):
        if len([x for x in self.line_ids if not x.account_move_id]) == 0:
            return
        vals = self.prepare_concepts_account_move_values()
        move = self.env['account.move'].create(vals)
        if move:
            move.action_post()
            print("Asientos Conceptos de Gastos: %s" % (move.name))
        else:
            msg = _("Error Creating Account Move")
            raise UserError(msg)

    def prepare_concepts_account_move_values(self):
        vals = {}
        vals['ref'] = "%s - %s" % (self.name, _("Expenses"))
        vals['journal_id'] = self.petty_cash_id.journal_id.id
        vals['date'] = self.date
        # vals['petty_cash_id'] = self.petty_cash_id.id
        vals['petty_cash_sheet_id'] = self.id

        lines = []
        dtotal = 0
        for line in self.line_ids:
            # Prepare values only for expenses not for invoices
            if line.require_invoice:
                continue
            dvals = {}
            dvals['account_id'] = line.account_id.id
            # dvals['analytic_account_id'] = line.analytic_account_id.id
            dvals['name'] = line.concept_id.name
            dvals['debit'] = line.price_total
            lines.append((0, 0, dvals))
            dtotal += line.price_total

        cvals = {}
        credit_account = self.petty_cash_id.account_id
        if self.petty_cash_type == 'reposition':
            if self.advance_payment_id:
                credit_account = self.advance_payment_id.destination_account_id
            else:
                credit_account = self.petty_cash_id.account_id
        cvals['account_id'] = credit_account.id
        cvals['name'] = credit_account.name
        cvals['credit'] = dtotal
        lines.append((0, 0, cvals))
        vals['line_ids'] = lines
        return vals

    def create_invoice_payments_move(self):
        if len([x for x in self.line_ids if x.account_move_id]) == 0:
            return
        vals = self.prepare_invoice_payment_values()
        move = self.env['account.move'].create(vals)
        if move:
            move.action_post()
            print("Asientos Facturas de Gastos: %s" % (move.name))
        else:
            msg = _("Error Creating Account Move")
            raise UserError(msg)
        return move

    def prepare_invoice_payment_values(self):
        vals = {}
        vals['ref'] = "%s - %s" % (self.name, _("Invoices"))
        vals['journal_id'] = self.petty_cash_id.journal_id.id
        vals['date'] = self.date
        vals['petty_cash_sheet_id'] = self.id

        lines = []
        dtotal = 0
        for line in self.line_ids:
            if not line.require_invoice:
                continue
            payable_lines = line.get_payable_move_lines()
            for pline in payable_lines:
                dvals = {}
                dvals['account_id'] = pline.account_id.id
                dvals['date'] = pline.date
                # dvals['analytic_account_id'] = pline.analytic_account_id.id
                dvals['name'] = pline.name or pline.account_id.name
                dvals['partner_id'] = pline.partner_id.id
                dvals['internal_note'] = "PettyCashSheetLineId:%s" % (line.id)
                dvals['debit'] = line.price_total
                lines.append((0, 0, dvals))
                dtotal += line.price_total

        cvals = {}
        credit_account = self.petty_cash_id.account_id
        if self.petty_cash_type == 'reposition':
            if self.advance_payment_id:
                credit_account = self.advance_payment_id.destination_account_id
            else:
                credit_account = self.petty_cash_id.account_id
        elif self.petty_cash_type == 'fixed':
            credit_account = self.petty_cash_id.account_id
        cvals['account_id'] = credit_account.id
        cvals['name'] = credit_account.name
        cvals['credit'] = dtotal
        lines.append((0, 0, cvals))
        vals['line_ids'] = lines
        return vals

    def reconcile_invoices_payments(self, move):
        if not move:
            return
        for line in move.line_ids:
            if line.internal_note and line.internal_note.startswith("PettyCashSheetLineId"):
                pcslid = int(line.internal_note.split(":")[1])
                sheet_line = self.env['petty.cash.sheet.line'].browse(pcslid)
                payable_lines = sheet_line.get_payable_move_lines()
                payable_move_lines = self.env['account.move.line'].browse([x.id for x in payable_lines])
                (payable_move_lines + line).reconcile()
                print("Conciliando %s" % (sheet_line.account_move_id.name))

    def append_invoice(self):
        vals = {}
        vals['date'] = self.date
        vals['petty_cash_sheet_id'] = self.id
        vals['company_id'] = self.company_id.id
        wizard = self.env['petty.cash.sheet.create.invoice'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Append Invoice'),
            'target'   : 'new',
            'view_mode': 'form',
            'res_model': 'petty.cash.sheet.create.invoice',
            'res_id'   : wizard.id
        }

    def open_invoices(self):
        moves = self.env['account.move'].search(
                [
                    ('petty_cash_sheet_id', '=', self.id),
                    ('move_type', '=', 'in_invoice')
                ]
        )
        if moves:
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Invoices'),
                'target'   : 'current',
                'view_mode': 'list,form',
                'res_model': 'account.move',
                'domain'   : [('id', 'in', [x.id for x in moves])]
            }

    def open_account_moves(self):
        moves = self.env['account.move'].search(
                [
                    ('petty_cash_sheet_id', '=', self.id),
                    ('move_type', '=', 'entry')
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

    @api.model
    def _create_sequences(self):
        template_company = self.env.ref('base.main_company')
        template_sequence = self.env['ir.sequence'].search(
                [
                    ('code', '=', 'petty.cash.sheet'),
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


class PettyCashSheetLine(models.Model):
    _name = 'petty.cash.sheet.line'
    _description = "Expense Detail"

    sheet_id = fields.Many2one('petty.cash.sheet', string="Sheet Id", ondelete='cascade')
    name = fields.Char("Description")
    concept_id = fields.Many2one('petty.cash.concept', string="Concept", required=True)
    require_invoice = fields.Boolean("Require Invoice", related="concept_id.require_invoice")
    account_move_id = fields.Many2one('account.move', string="Invoice",
                                      domain=[('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
                                              ('state', '=', 'posted'),
                                              ('payment_state', 'in', ['not_paid', 'partial'])])
    invoice_total = fields.Monetary("Invoice Total", related='account_move_id.amount_total')
    invoice_balance = fields.Monetary('Invoice Balance')
    account_move_amount = fields.Monetary('Invoice Amount', compute='_compute_account_move_amount')
    date = fields.Date("Date", default=lambda self: self.sheet_id.date)
    partner_id = fields.Many2one('res.partner', string="Partner")
    account_id = fields.Many2one('account.account', string="Account")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    quantity = fields.Float("Qty.", default=1, required=True)
    price_unit = fields.Monetary("Price Unit", required=True)
    currency_id = fields.Many2one('res.currency', related='sheet_id.currency_id')
    price_total = fields.Monetary('Price Total', compute="_compute_price_total")

    @api.onchange('concept_id')
    def _onchange_concept_id(self):
        self.account_id = self.concept_id.account_id
        self.analytic_account_id = self.concept_id.analytic_account_id.id
        self.price_unit = self.concept_id.amount
        self.date = self.sheet_id.date
        self.name = self.concept_id.name
        self.account_move_id = False
        self.partner_id = False
        self.quantity = 1

    @api.onchange('account_move_id')
    def _onchange_account_move_id(self):
        if self.account_move_id:
            self.date = self.account_move_id.invoice_date
            self.account_id = False
            self.analytic_account_id = False
            self.partner_id = self.account_move_id.partner_id.id
            self.quantity = 1
            self.invoice_balance = self.account_move_id.amount_residual
            self.price_unit = self.account_move_id.amount_residual
            self.currency_id = self.account_move_id.currency_id.id

    @api.depends('price_unit', 'quantity')
    def _compute_price_total(self):
        for record in self:
            record.price_total = record.price_unit * record.quantity

    @api.depends('account_move_id.payment_state')
    def _compute_account_move_amount(self):
        for record in self:
            if record.account_move_id.payment_state == 'not_paid':
                record.account_move_amount = record.account_move_id.amount_residual
            else:
                record.account_move_amount = record.account_move_id.amount_total

    def get_payable_move_lines(self):
        if not self.account_move_id:
            return None
        lines = []
        for move_line in self.account_move_id.line_ids:
            if move_line.account_id.account_type == 'liability_payable':
                lines.append(move_line)
        return lines
