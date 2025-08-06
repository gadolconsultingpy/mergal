from odoo import api, fields, models, _
from odoo.http import request


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    # def try_loading(self, company=False):
    #     """ Installs this chart of accounts for the current company if not chart
    #     of accounts had been created for it yet.
    #     """
    #     # do not use `request.env` here, it can cause deadlocks
    #     if not company:
    #         if request and hasattr(request, 'allowed_company_ids'):
    #             company = self.env['res.company'].browse(request.allowed_company_ids[0])
    #         else:
    #             company = self.env.company
    #     # If we don't have any chart of account on this company, install this chart of account
    #     if not company.chart_template_id and not self.existing_accounting(company):
    #         for template in self:
    #             template.with_context(default_company_id=company.id)._load(company)
