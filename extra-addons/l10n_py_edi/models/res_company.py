from odoo import api, models, fields
import pytz

_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


def _tz_get(self):
    return _tzs


class ResCompany(models.Model):
    _inherit = 'res.company'

    sifen_environment = fields.Selection(
            [
                ('X', 'Disabled'),
                ('0', 'Test'),
                ('1', 'Production'),
            ], default='X', string="SIFEN Environment", tracking=True
    )
    schema_version = fields.Char("Schema Version", default="150", tracking=True)
    tz = fields.Selection(_tz_get, string='Timezone', default="America/Asuncion", tracking=True)
    certificate_id = fields.Many2one('edi.certificate', string="Certificate")
    security_code_1 = fields.Char("Security Code 1", tracking=True)
    security_code_2 = fields.Char("Security Code 2", tracking=True)
