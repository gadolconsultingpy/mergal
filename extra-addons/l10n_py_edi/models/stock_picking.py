import base64
import datetime
import tempfile

import qrcode
from odoo import api, models, fields, _
import random

from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _default_transaction_type(self):
        return self.env['edi.transaction.type'].search([('code', '=', '1')]).id

    def _default_tax_type(self):
        return self.env['account.tax.type'].search([('code', '=', '1')]).id

    def _default_presence_id(self):
        return self.env['edi.presence'].search([('code', '=', '1')], limit=1).id

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
    transaction_type_id = fields.Many2one('edi.transaction.type', string="Electronic Transaction Type",
                                          default=_default_transaction_type)
    edi_document_datetime = fields.Datetime("Document Date/Time", compute="_compute_edi_document_datetime", store=True)
    # tax_type_id = fields.Many2one('account.tax.type', string="Tax Type", default=_default_tax_type)
    # # is_local_currency = fields.Boolean("Is Local Currency", compute="_compute_is_local_currency")
    # currency_rate_condition = fields.Selection(
    #         [
    #             ('1', 'Global'),
    #             ('2', 'Por Item'),
    #         ], default='1', string="Currency Rate Condition"
    # )
    presence_id = fields.Many2one('edi.presence', string="Presence Indicator", default=_default_presence_id)
    issue_reason_id = fields.Many2one('edi.issue.reason.picking', string="Picking Issue Reason")
    # discount_total = fields.Monetary('Discount Total', compute="_compute_discount_total")
    # reverted_invoice_ids = fields.One2many('account.move.reverted', 'move_id', string="Reverted Invoices")
    qr_link = fields.Char("QR Link")
    qr_image = fields.Image("QR Image", compute="_compute_qr_image")
    journal_id = fields.Many2one('account.journal', string="Stock Journal")
    issue_responsible_id = fields.Many2one('edi.issue.responsible', string="Issue Responsible")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    driver_id = fields.Many2one('res.partner', string="Driver")
    sequence_number = fields.Char("Sequence Number")
    scheduled_invoice_date = fields.Date("Scheduled Invoice Date", compute="_compute_scheduled_invoice_date",
                                         store=True)
    related_invoice_id = fields.Many2one('account.move', compute="_compute_related_invoice_id")
    travel_distance = fields.Float("Travel Distance (Km)")
    sifen_environment = fields.Selection(related='company_id.sifen_environment', string="SIFEN Environment")
    contact_address = fields.Char(related='partner_id.contact_address')

    @api.depends('create_date')
    def _compute_edi_document_datetime(self):
        for rec in self:
            if rec.date_done and rec.create_date:
                if rec.create_date.date() > rec.date_done.date():
                    rec.edi_document_datetime = datetime.datetime.combine(rec.date_done,
                                                                          datetime.time(hour=23, minute=59, second=59))
                elif rec.create_date.date() < rec.date_done.date():
                    rec.edi_document_datetime = datetime.datetime.combine(rec.date_done,
                                                                          datetime.time(hour=0, minute=0, second=0))
                else:
                    rec.edi_document_datetime = datetime.datetime.combine(rec.date_done, rec.create_date.time())
            else:
                rec.edi_document_datetime = datetime.datetime.now()

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        self.driver_id = self.vehicle_id.driver_id.id

    def _compute_related_invoice_id(self):
        for rec in self:
            # inv = self.env['account.move'].search([('envio', '=', rec.id)])
            # if inv:
            #     rec.related_invoice_id = inv.id
            # else:
            rec.related_invoice_id = False

    def _compute_scheduled_invoice_date(self):
        for rec in self:
            # inv = self.env['account.move'].search(
            #         [
            #             ('envio', '=', rec.id),
            #             ('state', '=', 'posted'),
            #         ], limit=1, order="id desc"
            # )
            # if inv:
            #     rec.scheduled_invoice_date = inv.invoice_date
            # else:
            rec.scheduled_invoice_date = rec.scheduled_date

    def default_get(self, fields_list):
        vars = super(StockPicking, self).default_get(fields_list)
        vars['journal_id'] = self.env['account.journal'].search([('invoice_type_id.code', '=', '7')]).id
        vars['issue_reason_id'] = self.env['edi.issue.reason.picking'].search([('code', '=', '1')]).id
        vars['issue_responsible_id'] = self.env['edi.issue.responsible'].search([('code', '=', '1')]).id
        return vars

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        if self.picking_type_id.code == 'incoming':
            self.issue_reason_id = self.env['edi.issue.reason.picking'].search([('code', '=', '4')]).id
        elif self.picking_type_id.code == 'outgoing':
            self.issue_reason_id = self.env['edi.issue.reason.picking'].search([('code', '=', '1')]).id
        elif self.picking_type_id.code == 'internal':
            self.issue_reason_id = self.env['edi.issue.reason.picking'].search([('code', '=', '7')]).id
        if self.picking_type_id.edi_sequence_id:
            self.sequence_id = self.picking_type_id.edi_sequence_id.id

    def _compute_qr_image(self):
        # Encoding data using make() function
        img = qrcode.make(self.qr_link or self.name)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            img.save(temp_file.name)
        img_obj = open(temp_file.name, "rb")
        self.qr_image = base64.b64encode(img_obj.read())
        # Saving as an image file

    @api.depends('control_code')
    def _compute_control_code_graph(self):
        for rec in self:
            char = ""
            for pos, digit in enumerate(rec.control_code or "", start=1):
                char += digit
                if pos % 4 == 0:
                    char += " "
            rec.control_code_graph = char

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
        self.ensure_one()
        if self.sifen_environment == 'X':  # SIFEN FEATURES DISABLED
            return ""
        parts = []
        parts.append(self.journal_id.invoice_type_id.code.rjust(2, "0"))
        company_vat = self.company_id.vat or '0-0'
        parts.append(company_vat.split("-")[0].rjust(8, "0"))
        parts.append(company_vat.split("-")[1])
        parts.append(self.sequence_id.establishment.rjust(3, "0"))
        parts.append(self.sequence_id.issuance_point.rjust(3, "0"))
        parts.append(str(self.sequence_number).rjust(7, "0"))
        parts.append(self.company_id.tax_payer_type)
        if self.edi_document_datetime:
            parts.append(self.edi_document_datetime.strftime("%Y%m%d"))
        else:
            parts.append(fields.Date.context_today(self).strftime("%Y%m%d"))
        parts.append(self.issue_type)
        parts.append(self.security_code)
        _logger.info("NUMERO : %s" % ("".join(parts)))
        code = "".join(parts)
        modulus = self.calculate_modulus(code, 11)
        parts.append(str(modulus))
        code = "".join(parts)
        return code

    def generate_code_of_control(self, force=False):
        _logger.info("generate_code_of_control: force %s" %(force))
        if not self.control_code or force:
            self.control_code = self.get_code_of_control()

    def calculate_modulus(self, value, basemax):
        digit_sum = 0
        k = 2
        for pos, digit in enumerate(reversed(str(value)), start=1):
            if k > basemax:
                k = 2
            digit_sum += (int(digit) * k)
            k += 1

        rest = digit_sum % basemax
        if rest > 1:
            modulus = basemax - rest
        else:
            modulus = 0
        return modulus

    def generate_security_code(self, force=False):
        self.ensure_one()
        if self.sifen_environment == 'X':  # SIFEN FEATURES DISABLED
            return
        code = str(random.randint(1, 999999999))
        if not self.security_code or force:
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

    def business_type(self):
        types = {'B2B': '1',
                 'B2C': '2',
                 'B2G': '3',
                 'B2F': '4'}
        return types.get("B2%s" % (self.partner_id.parent_id.business_partner_type or
                                   self.partner_id.business_partner_type), "2")

    def _search_sequence_id(self, wh_code, pick_code):
        picking_type = self.env['stock.picking.type'].search(
                [
                    ('warehouse_id.code', '=', wh_code),
                    ('sequence_code', '=', pick_code),
                ]
        )
        if picking_type:
            self.sequence_id = picking_type.edi_sequence_id.id
            if not self.env.context.get("set_name_from_api", False):
                next_seq = self.sequence_id.next_by_id(sequence_date=self.date_done)
                _logger.info("NEXT PICKING SEQ: %s" % (next_seq))
                self.name = next_seq
            self.sequence_number = self.name.split("-")[-1]
            if not self.journal_id:
                self.journal_id = self.sequence_id.journal_id.id

    def button_validate(self):
        for rec in self:
            if rec.sifen_environment == 'X':    #SIFEN FEATURES DISABLED
                continue
            if rec.picking_type_id.edi_sequence_id and not rec.sequence_id:
                rec.sequence_id = rec.picking_type_id.edi_sequence_id.id
                if not rec.env.context.get("set_name_from_api", False):
                    next_seq = rec.sequence_id.next_by_id(sequence_date=rec.date_done)
                    _logger.info("NEXT PICKING SEQ: %s" % (next_seq))
                    if not rec.name:
                        rec.name = next_seq
                rec.sequence_number = rec.name.split("-")[-1]
                if not rec.journal_id:
                    rec.journal_id = rec.sequence_id.journal_id.id
            if rec.sequence_id:
                if not rec.issue_reason_id:
                    msg = _("Missing Reason for Transfer")
                    raise UserError(msg)
                if not rec.vehicle_id or not rec.driver_id:
                    msg = _("Missing Vehicle/Driver Data")
                    raise UserError(msg)
                if not rec.issue_responsible_id:
                    rec.issue_responsible_id = rec.env['edi.issue.responsible'].search([('code', '=', '1')])
                rec.sequence_number = rec.name.split("-")[-1]
                rec.generate_security_code()
                rec.generate_code_of_control()
        res = super(StockPicking, self).button_validate()
        return res

    def generate_codes(self):
        self.sequence_number = self.name.split("-")[-1]
        self.generate_security_code()
        self.generate_code_of_control()

    @api.onchange('sequence_id')
    def _onchange_sequence_id(self):
        if self.sequence_id:
            if self.sequence_id.journal_id:
                self.journal_id = self.sequence_id.journal_id.id


class StockPickingMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def get_edi_line_inf(self):
        if self.lot_id.name:
            return "Lote: %s, Vencimiento: None" % (self.lot_id.name)
        return "--"
        # return "Lote: %s, Vencimiento: %s" % (self.lot_id.name, self.lot_id.expiration_date)
