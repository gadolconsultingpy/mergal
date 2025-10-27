from odoo import api, models, fields, _
import pytz

_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


def _tz_get(self):
    return _tzs


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def default_get(self, fields):
        vals = super(ResConfigSettings, self).default_get(fields)
        company = self.env['res.company'].search([('id', '=', vals.get('company_id'))], limit=1)
        if company:
            for field in self.get_extended_fields():
                vals[field] = company[field]
        return vals

    schema_version = fields.Char("Schema Version")
    tz = fields.Selection(_tz_get, string='Timezone')

    def execute(self):
        """
        Called when settings are saved.

        This method will call `set_values` and will install/uninstall any modules defined by
        `module_` Boolean fields and then trigger a web client reload.

        .. warning::

            This method **SHOULD NOT** be overridden, in most cases what you want to override is
            `~set_values()` since `~execute()` does little more than simply call `~set_values()`.

            The part that installs/uninstalls modules **MUST ALWAYS** be at the end of the
            transaction, otherwise there's a big risk of registry <-> database desynchronisation.
        """
        super(ResConfigSettings, self).execute()
        cval = {}
        for field in self.get_extended_fields():
            cval[field] = self[field]
        self.company_id.write(cval)
        return {
            'type': 'ir.actions.client',
            'tag' : 'reload',
        }

    @api.model
    def get_extended_fields(self):
        return ['schema_version', 'tz']
