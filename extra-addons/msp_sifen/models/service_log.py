from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ServiceLog(models.Model):
    _inherit = 'service.log'

    edi_event_id = fields.Many2one('edi.event')

    def get_updatable_fields(self):
        fields = super(ServiceLog, self).get_updatable_fields()
        fields.append("edi_event_id")
        return fields

    def run_python(self):
        python = self.env['python.interpreter'].search(
                [
                    ('name', '=', 'service.log')
                ]
        )
        if python:
            try:
                python.execute(objects={'record': self})
            except BaseException as errstr:
                msg = _("Error executing Python code: %s") % (errstr)
                raise UserError(msg)

