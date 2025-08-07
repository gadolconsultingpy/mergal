from odoo import _, fields, models, api
import logging

_logger = logging.getLogger(__name__)


class RecConfigCustom(models.Model):
    _name = 'res.config.custom'
    _description = 'Additional Parameters'

    name = fields.Char("Name", compute="_compute_name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)

    _sql_constraints = [('unique_per_company', 'unique(company_id)', 'This setting must be unique by Company')]

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "%s - %s" % (rec.company_id.name, _("Additional Parameters"))

    @api.model
    def get_company_custom_config(self, company_id=None):
        if not company_id:
            config = self.env[self._name].search([('company_id', '=', self.env.user.company_id.id)], order="id")
        else:
            config = self.env[self._name].search([('company_id', '=', company_id)])
        if not config:
            _logger.warning(_("Company Custom Config Not Found"))
        return config
