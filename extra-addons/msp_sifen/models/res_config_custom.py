from odoo import api, models, fields, _


class ResConfigCustom(models.Model):
    _inherit = 'res.config.custom'

    invoice_batch = fields.Boolean("Send Invoice in Batch")
    invoice_batch_limit = fields.Integer("Invoice Batch Limit", default="50")
    invoice_batch_delay = fields.Integer("Invoice Batch Delay in Minutes", default="60")
    edi_delayed_send_days = fields.Integer('EDI Delayed Send Days', default=3)
    edi_only_send_to_partner = fields.Boolean("Send If Partner has Mail")

    edi_send_mode = fields.Selection(
            [
                ('disable', 'Disable'),
                ('test', 'Test (Default Email)'),
                ('production', 'Production')
            ], default='disable', string="Send Environment"
    )
    edi_missing_email = fields.Selection(
            [
                ('skip', 'Do not send'),
                ('template', 'Template Email'),
                ('default', 'Default Email'),
            ], default='skip', string='When Missing Email'
    )
    test_email = fields.Char("Default Email", default="'Martin Salcedo' <martinsalcedo.apps@gmail.com>")

    def backup_procedures(self):
        controllers = self.env['service.controller.procedure'].search([])
        for control in controllers:
            control.backup_record()
        procedures = self.env['edi.procedure'].search([])
        for proc in procedures:
            proc.backup_record()
