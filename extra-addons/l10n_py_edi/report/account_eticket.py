from odoo import api, models, fields, _


class AccountETicket(models.AbstractModel):
    _name = "report.l10n_py_edi.account_eticket_report"
    _description = 'Electronic Ticket Report'

    def _get_report_values(self, docids, data={}):
        # ensure one (paper format does not have paper cut)
        if len(docids) > 1:
            docids = docids[0]
        invoice = self.env['account.move'].browse(docids)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('l10n_py_edi.account_eticket')
        config = self.env['res.config.custom'].search([('company_id', '=', invoice.company_id.id)])
        # for vat in invoice.amount_by_group:
        #     print(vat)
        docargs = {
            'doc_ids'  : docids,
            'doc_model': report.model,
            'docs'     : invoice,
            'company'  : invoice.company_id,
            'config'   : config,
        }
        return docargs
