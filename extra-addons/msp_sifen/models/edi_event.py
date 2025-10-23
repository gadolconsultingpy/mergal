from odoo import api, models, fields, _
import logging
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# from odoo.tools.misc import profile

_logger = logging.getLogger(__name__)
try:
    from lxml import etree
except BaseException as errstr:
    _logger.warning("Can't import etree library")


class EDIEvent(models.Model):
    _inherit = ['mail.thread']
    _name = 'edi.event'
    _description = 'EDI Event'
    _order = 'id desc'

    name = fields.Char("Name")
    type = fields.Selection(
            [
                ('de', 'Send DE'),
                ('de_batch', 'Send DE in Batch'),
                ('de_consult', 'Consult DE'),
                ('de_batch_consult', 'Consult DE Batch'),
                ('vat_consult', 'VAT Consult'),
                ('de_cancel', 'DE Cancellation'),
                ('de_invalid', 'DE Invalidate'),
                ('nomination', 'Nomination'),
            ], default='de', string="Event Type"
    )
    procedure_id = fields.Many2one('edi.procedure', string="Procedure")
    res_model = fields.Char("Res. Model")
    res_id = fields.Integer("Res. Id")
    res_name = fields.Char("Res. Name")
    url = fields.Char("URL", tracking=True)
    headers = fields.Text("Headers")
    method = fields.Char("Method", tracking=True)
    soap_method = fields.Char("SOAP Method")
    state = fields.Selection(
            [
                ('pending', 'Pending'),
                ('sent', 'Sent'),
                ('finished', 'Finished'),
            ], default='pending', string="State"
    )
    request_content = fields.Binary("Request Content")
    request_filename = fields.Char("Request Filename")
    log_ids = fields.One2many('service.log', 'edi_event_id', string="Logs")
    company_id = fields.Many2one('res.company', string="Company")

    def default_get(self, fields_list):
        vals = super(EDIEvent, self).default_get(fields_list)
        sequence = self.env['ir.sequence'].search([('code', '=', 'edi.event')])
        if not sequence:
            msg = _("Missing Sequence: %s" % ("edi.event"))
            raise UserError(msg)
        vals['name'] = sequence.next_by_id()
        return vals

    def open_origin(self):
        record = self.env[self.res_model].browse(self.res_id)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Event Origin'),
            'res_model': self.res_model,
            'view_mode': 'form',
            'res_id'   : record.id,
        }

    def finish(self):
        if self.state == 'sent':
            _logger.info("Finished Event: %s" % (self.name))
            self.state = 'finished'

    def process(self):
        if self.state == 'pending':
            _logger.info("Processing Event: %s" % (self.name))
            self.env['edi.procedure'].run_procedure(self, 'sifen.edi.event.%s' % (self.type))

    @api.model
    def _cron_process(self):
        events = self.env['edi.event'].search(
                [
                    ('state', '=', 'pending')
                ], order="id"
        )
        _logger.info("Events to process: %s" %(len(events)))
        for pnd in events:
            try:
                pnd.process()
            except BaseException as errstr:
                _logger.error("Error Processing Event: %s" %(errstr))
