from odoo import api, models, fields, _


class PettyCashSheetCreateInvoice(models.TransientModel):
    _name = 'petty.cash.sheet.create.invoice'
    _description = 'Create Invoice from Petty Cash'
    _check_company_auto = True

    date = fields.Date("Date")
    company_id = fields.Many2one('res.company', string="Company", required=True)
    petty_cash_sheet_id = fields.Many2one('petty.cash.sheet')
    concept_id = fields.Many2one('petty.cash.concept', string="Concept")
    partner_id = fields.Many2one('res.partner', string="Supplier")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    amount = fields.Monetary("Total Amount", compute="_compute_amount")
    amount_to_pay = fields.Monetary('Amount to Pay')
    invoice_id = fields.Many2one('account.move',
                                 domain=[('payment_state', 'in', ['not_paid', 'partial']),
                                         ('move_type', 'in', ['in_invoice', 'in_refund'])])
    add_type = fields.Selection(
            [
                ('new', 'New'),
                ('existing', 'Existing')
            ], default='new', string="Append Type"
    )
    deductible_amount = fields.Monetary("Deductible Amount")
    tax_lines = fields.One2many('petty.cash.sheet.create.invoice.tax', 'parent_id', string="Taxes")

    @api.depends('tax_lines')
    def _compute_amount(self):
        for rec in self:
            rec.amount = sum([x.price_total for x in rec.tax_lines])

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        self.amount = self.invoice_id.amount_residual
        self.amount_to_pay = self.invoice_id.amount_residual
        self.date = self.invoice_id.invoice_date
        self.partner_id = self.invoice_id.partner_id.id

    @api.onchange('concept_id')
    def _onchange_concept_id(self):
        self.deductible_amount = self.concept_id.deductible_amount

    def append_invoice(self):
        self.petty_cash_sheet_id.line_ids = [
            (0, 0,
             {
                 'concept_id'     : self.concept_id.id,
                 'name'           : self.concept_id.name,
                 'account_move_id': self.invoice_id.id,
                 'date'           : self.date,
                 'partner_id'     : self.invoice_id.partner_id.id,
                 'invoice_balance': self.invoice_id.amount_residual,
                 'quantity'       : 1,
                 'price_unit'     : self.amount_to_pay,
             })
        ]
        invoice = self.env['account.move'].browse(self.invoice_id.id)
        invoice.write({'petty_cash_sheet_id': self.petty_cash_sheet_id.id})

    def create_invoice(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        vals = {}
        vals['move_type'] = 'in_invoice'
        vals['invoice_date'] = self.date
        vals['petty_cash_sheet_id'] = self.petty_cash_sheet_id.id
        vals['partner_id'] = self.partner_id.id
        vals['journal_id'] = self.petty_cash_sheet_id.petty_cash_id.journal_id.id
        # Deductible
        vals['invoice_line_ids'] = [(5, 0, 0)]

        for taxes in self.tax_lines:
            # dvals = self.env['account.move.line']
            dvals = {}
            dvals['account_id'] = self.concept_id.account_id.id
            dvals['quantity'] = taxes.quantity
            dvals['price_unit'] = taxes.price_unit
            dvals['tax_ids'] = [taxes.tax_id.id]
            vals['invoice_line_ids'].append((0, 0, dvals))

        # dvals = {}
        # dvals['account_id'] = self.concept_id.account_id.id
        # dvals['quantity'] = 1
        # if self.deductible_amount and self.amount > self.deductible_amount:
        #     dvals['price_unit'] = self.deductible_amount
        # else:
        #     dvals['price_unit'] = self.amount
        # vals['invoice_line_ids'].append((0, 0, dvals))
        # if self.deductible_amount and self.amount > self.deductible_amount:
        #     Not Deductible
        #     ndvals = {}
        #     ndvals['account_id'] = config.not_deductible_account_id.id
        #     ndvals['quantity'] = 1
        #     ndvals['price_unit'] = self.amount - self.deductible_amount
        #     vals['invoice_line_ids'].append((0, 0, ndvals))

        invoice = self.env['account.move'].create(vals)
        self.petty_cash_sheet_id.line_ids = [
            (0, 0,
             {
                 'concept_id'     : self.concept_id.id,
                 'name'           : self.concept_id.name,
                 'account_move_id': invoice.id,
                 'date'           : self.date,
                 'partner_id'     : self.partner_id.id,
                 'quantity'       : 1,
                 'price_unit'     : self.amount,
             })
        ]
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Invoice'),
            'target'   : 'current',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id'   : invoice.id
        }


class PettyCashSheetCreateInvoiceTax(models.TransientModel):
    _name = 'petty.cash.sheet.create.invoice.tax'
    _description = 'Invoice Tax from Petty Cash'

    parent_id = fields.Many2one('petty.cash.sheet.create.invoice', ondelete='cascade')
    type_tax_use = fields.Selection(
            [
                ('sale', 'Sale'),
                ('purchase', 'Purchase'),
            ], default='purchase', string="Tax Type"
    )
    move_type = fields.Selection(
            [
                ('in_invoice', 'Purchase Invoice'),
                ('in_refund', 'Purchase Credit Note'),
                ('out_invoice', 'Sale Invoice'),
                ('out_refund', 'Sale Credit Note'),
            ], default='in_invoice', string="Invoice Type"
    )
    currency_id = fields.Many2one('res.currency', related='parent_id.currency_id')
    tax_id = fields.Many2one('account.tax', string="Tax")
    quantity = fields.Float("Quantity", default=1)
    price_unit = fields.Monetary("Price Unit")
    price_tax = fields.Monetary("Price Tax")
    price_subtotal = fields.Monetary('Price Subtotal')
    price_total = fields.Monetary("Price Total")

    @api.onchange('tax_id', 'price_unit', 'quantity')
    def _onchange_prices(self):
        sign = 1
        if self.move_type in ['in_refund', 'out_refund']:
            sign = -1
        taxes = self.tax_id.compute_all(price_unit=self.price_unit, currency=self.currency_id,
                                        quantity=self.quantity, handle_price_include=True)
        self.update({
            'price_tax'     : sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) * sign,
            'price_subtotal': taxes['total_excluded'] * sign,
            'price_total'   : taxes['total_included'] * sign,
        })
