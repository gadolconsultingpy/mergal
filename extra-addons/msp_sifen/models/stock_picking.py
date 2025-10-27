import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sifen_state = fields.Selection(
            [
                ('skip', "Skip"),
                ('pending', "Pending"),
                ('queue', "In Queue"),
                ('sent', "Sent in Batch"),
                ('approved', "Approved"),
                ('rejected', 'Rejected'),
                ('cancel', 'Cancelled'),
                ('invalid', 'Invalidated'),
            ], default='pending', string="SIFEN State", copy=False, tracking=True
    )
    sifen_state_code = fields.Char("SIFEN State Code", copy=False, tracking=True)
    sifen_state_message = fields.Text("SIFEN State Message", copy=False, tracking=True)
    sifen_authorization = fields.Char("SIFEN Authorization", copy=False, tracking=True)
    sifen_send_mode = fields.Char("SIFEN Send Mode", compute='_compute_sifen_send_mode')
    # Compatibility with invoice
    invoice_date = fields.Date(string="Document Date", compute="_compute_invoice_date")
    # EDI
    edi_event_qty = fields.Integer('EDI Events Qty', compute='_compute_edi_event_qty')
    edi_batch_qty = fields.Integer('EDI Batch Qty', compute='_compute_edi_batch_qty')

    def open_edi_events(self):
        event_ids = self.env['edi.event'].search(
                [
                    ('res_model', '=', self._name), ('res_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        for eve in event_ids:
            print("EVENTS", eve.id, eve.name)
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

    def open_edi_batch(self):
        query = "SELECT edi_batch_id "
        query += "FROM edi_batch_stock_picking_rel "
        query += "WHERE stock_picking_id = %s " % (self.id)
        self._cr.execute(query)
        batch_ids = [x['edi_batch_id'] for x in self._cr.dictfetchall()]
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('EDI Batch'),
                  'res_model': 'edi.batch'}
        if not batch_ids:
            return
        if len(batch_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = batch_ids[0]
        elif len(batch_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', [x for x in batch_ids])]
        return action

    def _compute_edi_event_qty(self):
        for rec in self:
            rec.edi_event_qty = self.env['edi.event'].search_count(
                    [('res_model', '=', self._name), ('res_id', '=', rec.id)])

    def _compute_edi_batch_qty(self):
        for rec in self:
            query = "SELECT COUNT(edi_batch_id) cnt "
            query += "FROM edi_batch_stock_picking_rel "
            query += "WHERE stock_picking_id = %s " % (rec.id)
            self._cr.execute(query)
            rec.edi_batch_qty = self._cr.dictfetchall()[0]['cnt']

    def _compute_invoice_date(self):
        for rec in self:
            rec.invoice_date = datetime.date(year=rec.scheduled_date.year, month=rec.scheduled_date.month,
                                             day=rec.scheduled_date.day)

    def _compute_sifen_send_mode(self):
        for rec in self:
            rec.sifen_send_mode = "de"
            setting = self.env['res.config.custom'].search([('company_id', '=', rec.company_id.id)])
            if setting:
                if setting.invoice_batch:
                    rec.sifen_send_mode = 'batch'

    def sifen_procedure(self, procedure='sifen.stock.picking.send'):
        self.env['edi.procedure'].run_procedure(record=self, procedure='sifen.stock.picking.check')
        ctx_proc = self.env.context.get('edi_procedure', procedure)
        self.env['edi.procedure'].run_procedure(record=self, procedure=ctx_proc)

    def button_validate(self):
        if self.picking_type_id.edi_sequence_id:
            self.env['edi.procedure'].run_procedure(record=self, procedure='sifen.stock.picking.check')
        return super(StockPicking, self).button_validate()

    @api.model
    def _cron_edi_send(self):
        companies = self.env['res.company'].search([])
        for comp in companies:
            config = self.env['res.config.custom'].get_company_custom_config(company_id=comp.id)
            if not config:
                continue
            date_limit = fields.Date.context_today(self) + datetime.timedelta(days=-config.edi_delayed_send_days)
            pickings = self.env['stock.picking'].search(
                    [
                        ('date_done', '>=', date_limit),
                        ('company_id', '=', comp.id),
                        ('state', '=', 'done'),
                        ('sequence_id', '!=', False),
                        ('sifen_state', '=', 'pending')
                    ], order="scheduled_date, id "
            )
            for pick in pickings:
                setting = self.env['res.config.custom'].search([('company_id', '=', pick.company_id.id)])
                if not setting:
                    msg = _("Setting for Send Picking Missing")
                    raise UserError(msg)
                _logger.info("Processing Picking: %s" % (pick.name))
                if not setting.invoice_batch:
                    pick.with_context(edi_procedure='sifen.stock.picking.prepare').sifen_procedure()
                else:
                    pick.with_context(edi_procedure='sifen.stock.picking.batch.prepare').sifen_procedure()
            pickings = self.env['stock.picking'].search(
                    [
                        ('date_done', '>=', date_limit),
                        ('company_id', '=', comp.id),
                        ('state', '=', 'done'),
                        ('sequence_id', '!=', False),
                        ('sifen_state', '=', 'sent')
                    ], order="scheduled_date, id "
            )
            for pick in pickings:
                setting = self.env['res.config.custom'].search([('company_id', '=', pick.company_id.id)])
                if not setting:
                    msg = _("Setting for Send Picking Missing")
                    raise UserError(msg)
                _logger.info("Processing Picking: %s" % (pick.name))
                pick.with_context(edi_procedure='sifen.stock.picking.consult').sifen_procedure()

    def send_edi_document(self):
        pass

    def sifen_notify(self, vals):
        pass
