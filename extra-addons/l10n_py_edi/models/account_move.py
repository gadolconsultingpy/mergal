import datetime
import tempfile

import qrcode

from odoo import api, models, fields, _
import random

from odoo.exceptions import UserError
import base64
import logging
from num2words import num2words
import html

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    issue_type = fields.Selection(
            [
                ('1', 'Normal'),
                ('2', 'Contingency'),
            ], default='1', copy=False
    )
    security_code = fields.Char("Security Code", copy=False, tracking=True)
    control_code = fields.Char("Code of Control", copy=False, tracking=True)
    control_code_graph = fields.Char("Control of Control Graph", compute="_compute_control_code_graph")
    # sequence_id = fields.Many2one('ir.sequence', string="Invoice Sequence")   #Move to l10n_py
    document_serial = fields.Char("Document Serial", compute="_compute_document_number")
    document_number = fields.Char("Document Number", compute="_compute_document_number")
    transaction_type_id = fields.Many2one('edi.transaction.type', string="Electronic Transaction Type")
    tax_type_id = fields.Many2one('account.tax.type', string="Tax Type")
    # is_local_currency = fields.Boolean("Is Local Currency", compute="_compute_is_local_currency")
    currency_rate_condition = fields.Selection(
            [
                ('1', 'Global'),
                ('2', 'Por Item'),
            ], default='1', string="Currency Rate Condition"
    )
    presence_id = fields.Many2one('edi.presence', string="Presence Indicator")
    issue_reason_id = fields.Many2one('edi.issue.reason', string="Issue Reason")
    reversal_reason = fields.Char("Reversal Reason", help="Reason for Reversal")
    discount_total = fields.Monetary('Discount Total', compute="_compute_discount_total")
    reverted_invoice_ids = fields.One2many('account.move.reverted', 'move_id', string="Reverted Invoices")
    qr_link = fields.Char("QR Link")
    qr_image = fields.Image("QR Image", compute="_compute_qr_image")
    comment = fields.Text('Comment')
    edi_invoice_datetime = fields.Datetime("EDI Invoice Datetime", compute="_compute_edi_document_datetime",
                                           store=True, copy=False)
    edi_document_datetime = fields.Datetime("EDI Document Datetime", compute="_compute_edi_document_datetime",
                                            store=True, copy=False)
    sifen_environment = fields.Selection(related='company_id.sifen_environment', string="SIFEN Environment", )

    @api.depends('invoice_date', 'create_date')
    def _compute_edi_document_datetime(self):
        for record in self:
            rec = record.sudo()
            rec.edi_document_datetime = rec._get_edi_document_datetime()
            rec.edi_invoice_datetime = rec.edi_document_datetime

    def _get_edi_document_datetime(self):
        if self.invoice_date and self.create_date:
            if self.create_date.date() > self.invoice_date:
                _logger.info("Case 1: create_date > invoice_date")
                return datetime.datetime.combine(self.invoice_date, datetime.time(23, 59, 59))
            elif self.create_date.date() < self.invoice_date:
                _logger.info("Case 2: create_date < invoice_date")
                return datetime.datetime.combine(self.invoice_date, datetime.time(12, 0, 0))
            else:
                _logger.info("Case 3: create_date == invoice_date")
                return datetime.datetime.combine(self.invoice_date, self.create_date.time())
        else:
            _logger.info("Case 4: No invoice_date or create_date")
            return fields.Datetime.now()

    def default_get(self, fields):
        vals = super(AccountMove, self).default_get(fields)
        main_company = self.env.ref('base.main_company')
        config = self.env['res.config.custom'].get_company_custom_config(company_id=main_company.id)
        if config:
            # El tipo de transacción se cambia nuevamente según el onchange de productos.
            vals['transaction_type_id'] = config.default_edi_transaction_type.id
            vals['tax_type_id'] = config.default_edi_tax_type.id
            vals['presence_id'] = config.default_edi_presence_id.id
        return vals

    @api.depends('qr_link')
    def _compute_qr_image(self):
        for rec in self:
            # Encoding data using make() function
            ekuatia_link = "https://ekuatia.set.gov.py/consultas/"
            if rec.company_id.sifen_environment == "0":
                ekuatia_link = 'https://ekuatia.set.gov.py/consultas-test/'
            img = qrcode.make(rec.qr_link or ekuatia_link)
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                img.save(temp_file.name)
            img_obj = open(temp_file.name, "rb")
            rec.qr_image = base64.b64encode(img_obj.read())
            # Saving as an image file

    @api.depends('amount_total')
    def _compute_discount_total(self):
        for rec in self:
            rec.discount_total = sum([item.discount_amount for item in rec.invoice_line_ids])

    _sql_constraints = [
        ('unique_security_code', 'unique(company_id,security_code)', 'The Security Code Must Be Unique'),
        ('unique_sequence_name', 'unique(company_id,move_type,sequence_id,name)', 'The Sequence Name Must Be Unique'),
    ]

    # @api.depends('currency_id', 'company_id')
    # def _compute_is_local_currency(self):
    #     for rec in self:
    #         rec.is_local_currency = rec.currency_id.id == rec.company_id.currency_id.id

    def invoice_date_text(self):
        month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre",
                       "Octubre", "Noviembre", "Diciembre"]
        return "Asunción, %s de %s del %s " % (self.invoice_date.day,
                                               month_names[self.invoice_date.month],
                                               self.invoice_date.year)

    @api.depends('name')
    def _compute_document_number(self):
        for rec in self:
            try:
                if len(rec.name.split("-")) == 4:
                    rec.document_serial = rec.name.split("-")[0]
                else:
                    rec.document_serial = ""
                rec.document_number = rec.name.split("-")[-1].rjust(7, "0")
            except:
                rec.document_serial = ""
                rec.document_number = "0".rjust(7, "0")

    def get_code_of_control(self):
        if self.sifen_environment == 'X':
            return ""
        parts = []
        parts.append(self.journal_id.invoice_type_id.code.rjust(2, "0"))
        company_vat = self.company_id.vat or '0-0'
        parts.append(company_vat.split("-")[0].rjust(8, "0"))
        parts.append(company_vat.split("-")[1])
        parts.append(self.sequence_id.establishment.rjust(3, "0"))
        parts.append(self.sequence_id.dispatch_point.rjust(3, "0"))
        parts.append(str(self.sequence_number).rjust(7, "0"))
        parts.append(self.company_id.tax_payer_type)
        parts.append(self.invoice_date.strftime("%Y%m%d"))
        parts.append(self.issue_type)
        parts.append(self.security_code)
        code = "".join(parts)
        modulus = self.calculate_modulus(code, 11)
        parts.append(str(modulus))
        code = "".join(parts)
        return code

    def generate_code_of_control(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if not config:
            msg = _("Missing Additional Parameters")
            raise UserError(msg)
        if self.invoice_date >= config.edi_start_date:
            self.control_code = self.get_code_of_control()

    @api.model
    def calculate_modulus(self, numero, basemax):
        codigo = 0
        numero_al = ""

        for i in range(1, len(numero) + 1):
            c = numero[i - 1]
            codigo = ord(c.upper())

            if not (codigo >= 48 and codigo <= 57):
                numero_al += str(codigo)
            else:
                numero_al += c

        k = 2
        total = 0

        for i in range(len(numero_al), 0, -1):
            if k > basemax:
                k = 2
            numero_aux = int(numero_al[i - 1])
            total += numero_aux * k
            k += 1

        resto = total % 11
        if resto > 1:
            digito = 11 - resto
        else:
            digito = 0

        return digito

    def generate_security_code(self):
        if self.sifen_environment == 'X':
            return
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if not config:
            msg = _("Missing Additional Parameters")
            raise UserError(msg)
        if self.invoice_date >= config.edi_start_date:
            code = str(random.randint(1, 999999999))
            if not self.security_code:
                self.security_code = code.rjust(9, "0")

    @api.depends('control_code')
    def _compute_control_code_graph(self):
        for rec in self:
            char = ""
            for pos, digit in enumerate(rec.control_code or "", start=1):
                char += digit
                if pos % 4 == 0:
                    char += " "
            rec.control_code_graph = char

    def action_post(self):  # OK
        for rec in self:
            if rec.sifen_environment != 'X':
                rec._validate_journal_for_move_type()
                rec._validate_payment_term()
                # _logger.info("Invoice Date %s" % (rec.invoice_date))
                rec.edi_document_check()
        return super(AccountMove, self).action_post()

    def _validate_journal_for_move_type(self):
        if self.move_type == 'out_invoice' and self.journal_id.invoice_type_id.code not in ['1', 'X']:
            _logger.error("Invalid Journal for Out Invoice: %s" % (self.journal_id.name))
            raise UserError(_("Invalid Journal for Out Invoice"))
        if self.move_type == 'out_refund' and self.journal_id.invoice_type_id.code not in ['5', 'X']:
            _logger.error("Invalid Journal for Out Refund: %s" % (self.journal_id.name))
            raise UserError(_("Invalid Journal for Out Refund"))

    def _validate_payment_term(self):
        if self.move_type in ['out_invoice', 'out_refund']:
            if not self.invoice_payment_term_id:
                _logger.error("Missing Payment Term: %s" % (self.invoice_payment_term_id))
                raise UserError(_("Missing Payment Term"))

    def _generate_codes(self):
        self.generate_security_code()
        self.generate_code_of_control()

    def _post(self, soft=False):
        posted = super(AccountMove, self)._post(soft=soft)
        for rec in posted:
            if rec.move_type in ['out_refund', 'out_invoice']:
                rec.generate_security_code()
                rec.generate_code_of_control()
        return posted

    def edi_document_check(self):
        self.ensure_one()
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if not config:
            msg = _("Missing Additional Parameters")
            raise UserError(msg)
        _logger.info([self.invoice_date, config.edi_start_date])
        if self.invoice_date >= config.edi_start_date:
            if self.move_type in ['out_invoice', 'out_refund']:
                mfields = ['transaction_type_id', 'tax_type_id', 'presence_id']
                if self.move_type == 'out_refund':
                    mfields.append("issue_reason_id")
                    if not self.reverted_invoice_ids:
                        mfields.append("reversed_entry_id")
                for fn in mfields:
                    value = getattr(self, fn)
                    if not value:
                        fieldlabel = self._fields[fn].get_description(self.env).get('string')
                        msg = _("Field is Mandatory")
                        raise UserError("%s: %s" % (msg, fieldlabel))

    @api.onchange('invoice_line_ids')
    def _onchange_for_transaction_type_id(self):
        product_types = set([x.product_id._get_type() for x in self.invoice_line_ids])
        # print(product_types)
        transaction_type = "0"
        if "service" in product_types and "consu" in product_types:
            transaction_type = "3"
        elif "service" in product_types:
            transaction_type = "2"
        elif "consu" in product_types:
            transaction_type = "1"
        if transaction_type == "0":
            transaction_type = "1"
        self.transaction_type_id = self.env['edi.transaction.type'].search([('code', '=', transaction_type)])

    def get_amount_total_text(self):
        return "%s %s" % (
            self.currency_id.plural_name.upper(), num2words(self.amount_total, lang=self.env.user.lang[:2]).upper())


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    price_unit_with_discount = fields.Float('Price w/ Disc.', compute='_compute_price_unit_with_discount')
    # E721 - dPUniProSer
    price_unit_with_tax = fields.Float("Price w/ Tax", compute="_compute_price_unit_with_tax",
                                       help="E721 - dPUniProSer")
    # E727 - dTotBruOpeItem
    price_total_with_tax = fields.Float("Price Total w/ Tax", compute="_compute_price_total_with_tax",
                                        help="E727 - dTotBruOpeItem")
    # EA008 - dTotOpeItem
    price_subtotal_with_tax = fields.Float("Price Subtotal w/ Tax", compute="_compute_price_subtotal_with_tax",
                                           help="EA008 - dTotOpeItem")
    # E735 - dBasGravIVA
    taxable_subtotal = fields.Float("Taxable Subtotal", compute="_compute_taxable_subtotal", help="E735 - dBasGravIVA")
    # E736 - dLiqIVAItem
    tax_total = fields.Float("Tax Total", compute="_compute_tax_total", help="E736 - dLiqIVAItem")
    # EA002 - dDescItem
    unit_discount_amount = fields.Float('Uni Discount Amount', compute="_compute_unit_discount_amount",
                                        help="EA002 - dDescItem")

    discount_amount = fields.Float('Discount Amount', compute="_compute_discount_amount", digits=[15, 5])

    # E711  = quantity
    # EA003 = discount ( % )

    @api.depends('price_total')
    def _compute_price_unit_with_tax(self):
        for rec in self:
            if rec.quantity and rec.price_total:
                price_unit = rec.price_unit * 100000
                tax_info = rec.tax_ids.compute_all(price_unit,
                                                   quantity=1.0,
                                                   currency=rec.currency_id,
                                                   product=rec.product_id,
                                                   partner=rec.move_id.partner_id)
                # E721 - dPUniProSer
                rec.price_unit_with_tax = tax_info.get('total_included', 0) / 100000
            else:
                rec.price_unit_with_tax = 0.0

    @api.depends('price_unit', 'quantity')
    def _compute_price_total_with_tax(self):
        for rec in self:
            # E727
            rec.price_total_with_tax = rec.price_unit_with_tax * rec.quantity

    @api.depends('price_unit_with_tax', 'quantity')
    def _compute_unit_discount_amount(self):
        for rec in self:
            # EA002
            rec.unit_discount_amount = rec.price_unit_with_tax * (rec.discount / 100)

    @api.depends('price_unit', 'quantity')
    def _compute_price_subtotal_with_tax(self):
        for rec in self:
            # EA008 = (E721 - EA002) * E711

            # (   E721(Precio unitario)
            #     – EA002(Descuento; particular)
            #     – EA004(Descuentoglobal)
            #     – EA006(Anticipo;particular)
            #     – EA007(Anticipoglobal)
            # ) * E711(cantidad)
            rec.price_subtotal_with_tax = rec.currency_id.round(
                    (rec.price_unit_with_tax - rec.unit_discount_amount) * rec.quantity)

    @api.depends('price_unit_with_tax', 'quantity')
    def _compute_discount_amount(self):
        for rec in self:
            rec.discount_amount = (rec.price_unit_with_tax * rec.quantity) * (rec.discount / 100)

    # @api.onchange('discount')
    # def _onchange_discount_amount(self):
    #     self.discount_amount = (self.price_unit_with_tax * self.quantity) * (self.discount / 100)

    @api.depends('price_total')
    def _compute_tax_total(self):
        for rec in self:
            rec.tax_total = rec.price_total - rec.price_subtotal

    @api.depends('price_unit', 'price_subtotal')
    def _compute_price_unit_with_discount(self):
        for rec in self:
            if rec.quantity and rec.price_subtotal:
                rec.price_unit_with_discount = rec.price_subtotal / rec.quantity
            else:
                rec.price_unit_with_discount = 0.0

    @api.depends('tax_ids', 'price_subtotal_with_tax')
    def _compute_taxable_subtotal(self):
        for rec in self:
            if rec.tax_ids:
                tax_id = rec.tax_ids[0]
                tax_factor = 1 + (tax_id.amount / 100)
                # E735 = (EA008 * (E733/100)) / 1.1
                rec.taxable_subtotal = rec.price_subtotal_with_tax * (tax_id.taxable_percent / 100.0) / tax_factor
            else:
                rec.taxable_subtotal = rec.price_subtotal_with_tax

    def get_sale_values(self):
        # 1  - Exento
        # 2  - 5 %
        # 3  - 10 %
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        sale_values = [0, 0, 0, 0]
        for tf in [1, 2, 3]:
            tax_field = f"tax{tf}_id"
            config_tax_id = getattr(config, tax_field).id
            if self.tax_ids[0].id == config_tax_id:
                sale_values[tf] = self.price_total
            else:
                sale_values[tf] = 0
        return sale_values

    def get_edi_name(self):
        if self.product_id.default_code:
            offset = "[%s]" % (self.product_id.default_code)
            return self.name[len(offset):].replace("\n", " - ").strip()
        return self.name.replace("\n", " - ").strip()

    def get_escaped_name(self):
        return html.escape(self.get_edi_name())


class AccountMoveReversion(models.Model):
    _name = 'account.move.reverted'
    _description = 'Account Move Reverted'

    move_id = fields.Many2one('account.move', string="Reversion Move", ondelete='cascade')
    reversion_document_type = fields.Selection(
            [
                ('1', 'Electrónico'),
                ('2', 'Impreso'),
            ], string="Reversion Document Type", default='1'
    )
    reverted_cdc = fields.Char("Reverted CDC")
    reverted_stamped_number = fields.Char("Reverted Stamped Number")
    reverted_invoice_establishment = fields.Char("Reverted Invoice Establishment", size=3)
    reverted_invoice_dispatch_point = fields.Char("Reverted Invoice Dispatch Point", size=3)
    reverted_invoice_number = fields.Char("Reverted Invoice Number", size=7)
    reverted_invoice_full_number = fields.Char("Reverted Invoice Full Number", compute="_compute_full_number")
    reverted_invoice_date = fields.Date("Reverted Invoice Date")
    reverted_invoice_type_id = fields.Many2one('edi.document.type', string="Reverted Transaction Type")

    @api.depends('reverted_cdc', 'reversion_document_type', 'reverted_invoice_dispatch_point',
                 'reverted_invoice_establishment',
                 'reverted_invoice_number')
    def _compute_full_number(self):
        for rec in self:
            rec.reverted_invoice_full_number = "000-000-0000000"
            if rec.reversion_document_type == "1" and rec.reverted_cdc:
                rev_inv = self.env['account.move'].search([('control_code', '=', rec.reverted_cdc)])
                if rev_inv:
                    rec.reverted_invoice_full_number = rev_inv.name
                else:
                    import re
                    cadena = rec.reverted_cdc
                    pattern = re.compile(
                            r"(?P<tipo_documento>\d{2})"
                            r"(?P<ruc_emisor>\d{8})"
                            r"(?P<dv_emisor>\d{1})"
                            r"(?P<establecimiento>\d{3})"
                            r"(?P<punto_expedicion>\d{3})"
                            r"(?P<num_documento>\d{7})"
                            r"(?P<tipo_contribuyente>\d{1})"
                            r"(?P<fecha_emision>\d{8})"
                            r"(?P<tipo_emision>\d{1})"
                            r"(?P<codigo_seguridad>\d{9})"
                            r"(?P<digito_verificador>\d{1})"
                    )
                    match = pattern.match(cadena[:44])

                    if match:
                        _logger.info("Coincide con el patrón de CDC: %s" % rec.reverted_cdc)
                        rec.reverted_invoice_full_number = "%s-%s-%s" % (match.group('establecimiento') or '000',
                                                                         match.group('punto_expedicion') or '000',
                                                                         match.group('num_documento') or '0000000')
                    else:
                        _logger.info("No coincide con el patrón de CDC: %s" % rec.reverted_cdc)

            elif rec.reversion_document_type == "2":
                rec.reverted_invoice_full_number = "%s-%s-%s" % (rec.reverted_invoice_establishment or '000',
                                                                 rec.reverted_invoice_dispatch_point or '000',
                                                                 rec.reverted_invoice_number or '0000000')

    @api.onchange('reversion_document_type')
    def _onchange_reversion_document_type(self):
        if self.reversion_document_type == '2':
            if self.move_id.reversed_entry_id:
                # self.reverted_stamped_number = self.move_id.timbrado_id.name
                self.reverted_invoice_establishment = self.move_id.name.split("-")[0]
                self.reverted_invoice_dispatch_point = self.move_id.name.split("-")[1]
                self.reverted_invoice_number = self.move_id.name.split("-")[2]
                self.reverted_invoice_date = self.move_id.invoice_date
            else:
                self.reverted_stamped_number = False
                self.reverted_invoice_establishment = False
                self.reverted_invoice_dispatch_point = False
                self.reverted_invoice_number = False
                self.reverted_invoice_date = False

    @api.onchange('reverted_invoice_dispatch_point', 'reverted_invoice_establishment', 'reverted_invoice_number')
    def _onchange_reverted_invoice_full_number(self):
        if self.reverted_invoice_dispatch_point:
            self.reverted_invoice_dispatch_point = self.reverted_invoice_dispatch_point.rjust(3, "0")
        if self.reverted_invoice_establishment:
            self.reverted_invoice_establishment = self.reverted_invoice_establishment.rjust(3, "0")
        if self.reverted_invoice_number:
            self.reverted_invoice_number = self.reverted_invoice_number.rjust(7, "0")
