import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class EDIBatch(models.Model):
    _inherit = ['mail.thread']
    _name = 'edi.batch'
    _description = 'EDI Batch'
    _order = "create_date desc"

    name = fields.Char("Name")
    invoice_ids = fields.Many2many('account.move', string="Invoice Ids",
                                   domain="[('move_type','in',['out_refund','out_invoice'])]")
    picking_ids = fields.Many2many("stock.picking", string="Picking Ids",
                                   domain="[('picking_type_id.code','=','outgoing')]")
    lines_qty = fields.Integer("Lines Qty", compute='_compute_lines_qty')
    state = fields.Selection(
            [
                ('open', 'Open'),
                ('prepared', 'Prepared'),
                ('sent', 'Sent'),
            ], default='open', string="State"
    )
    move_type = fields.Selection(
            [
                ('out_invoice', 'Invoice'),
                ('out_refund', 'Credit Note'),
                ('stock_picking', 'Stock Picking'),
            ], default='out_invoice', string='Move Type'
    )
    expired = fields.Boolean("Expired")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id,
                                 required=True)
    sifen_state = fields.Selection(
            [
                ('skip', "Skip"),
                ('pending', "Pending"),
                ('queue', "In Queue"),
                ('sent', "Sent"),
                ('received', "Received"),
                ('finish', "Finished"),
                ('expire', "Expired"),
                ('rejected', 'Rejected'),
            ], default='pending', string="SIFEN State", copy=False, tracking=True
    )
    sifen_state_code = fields.Char("SIFEN State Code", copy=False, tracking=True)
    sifen_state_message = fields.Text("SIFEN State Message", copy=False, tracking=True)
    sifen_batch_nr = fields.Char("SIFEN Batch Nr.", tracking=True)
    edi_event_qty = fields.Integer("EDI Event Qty", compute='_compute_edi_event_qty')
    edi_event_ids = fields.One2many('edi.event', 'res_id', domain=[('res_model', '=', 'edi.batch')], string="Events")
    last_process_error = fields.Text("Last Process Error", copy=False, tracking=True)

    @api.depends('invoice_ids', 'picking_ids')
    def _compute_lines_qty(self):
        for rec in self:
            rec.lines_qty = len(rec.invoice_ids) + len(rec.picking_ids)

    def _compute_edi_event_qty(self):
        for rec in self:
            rec.edi_event_qty = self.env['edi.event'].search_count(
                    [('res_model', '=', self._name), ('res_id', '=', rec.id)])

    def open_edi_events(self):
        event_ids = self.env['edi.event'].search(
                [
                    ('res_model', '=', self._name), ('res_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        # for eve in event_ids:
        #     print("EVENTS", eve.id, eve.name)
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('EDI Events'),
                  'res_model': 'edi.event'}
        if len(event_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = event_ids.id
        elif len(event_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', event_ids.ids)]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sequence = self.env['ir.sequence'].search([('code', '=', 'EDIBatch')])
            if not sequence:
                msg = _("Missing Sequence: %s" % ("EDIBatch"))
                raise UserError(msg)
            vals["name"] = sequence.next_by_id()
        return super(EDIBatch, self).create(vals_list)

    def check_for_prepared(self):
        if self.state != 'open':
            return
        config = self.env['res.config.custom'].search([('company_id', '=', self.company_id.id)])
        if len(self.invoice_ids) == config.invoice_batch_limit or len(self.picking_ids) == config.invoice_batch_limit:
            _logger.info("Batch Prepared: %s, limit lines reached" % (self.name))
            self.state = 'prepared'
            return
        if (datetime.datetime.now() - self.create_date).seconds > (config.invoice_batch_delay * 60):
            _logger.info("Batch Prepared: %s, delay reached" % (self.name))
            self.state = 'prepared'
            return

    def send(self):
        if self.state == 'prepared':
            _logger.info("Sending Batch: %s" % (self.name))
            try:
                self.env['edi.procedure'].run_procedure(self, 'sifen.edi.batch.send')
                self.state = 'sent'
            except BaseException as errstr:
                _logger.error("Error Sending Batch: %s" % (self.name))
                _logger.error(errstr)
                self.last_process_error = str(errstr)

    def consult(self):
        if self.state == 'sent' and self.sifen_state == 'received':
            _logger.info("Sending Batch Consult: %s" % (self.name))
            self.env['edi.procedure'].run_procedure(self, 'sifen.edi.batch.consult')

    def action_prepared(self):
        self.state = 'prepared'

    def in_queue(self):
        if self.state == 'prepared' or (self.state == 'sent' and self.sifen_state == 'received'):
            self.sifen_state = 'queue'

    @api.model
    def _cron_edi_prepare(self):
        batch_list = self.env['edi.batch'].search(
                [
                    ('state', '=', 'open')
                ], order="id"
        )
        for batch in batch_list:
            batch.check_for_prepared()
            batch.send()
        batch_list = self.env['edi.batch'].search(
                [
                    ('state', '=', 'prepared'),
                    ('sifen_state', '=', 'pending'),
                ], order="id"
        )
        for batch in batch_list:
            batch.send()

    @api.model
    def _cron_edi_consult(self):
        batch_list = self.env['edi.batch'].search(
                [
                    ('sifen_state', '=', 'received')
                ], order="id"
        )
        for batch in batch_list:
            batch.consult()
