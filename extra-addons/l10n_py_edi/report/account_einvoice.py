from odoo import api, models, fields, _


class AccountEInvoice(models.AbstractModel):
    _name = 'report.l10n_py_edi.account_einvoice'
    _description = "Electronic Invoice"

    def _get_report_values(self, docids, data={}):
        # ensure one (paper format does not have paper cut)
        if len(docids) > 1:
            docids = docids[0]
        invoice = self.env['account.move'].browse(docids)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('l10n_py_edi.account_einvoice')
        config = self.env['res.config.custom'].search([('company_id', '=', invoice.company_id.id)])
        docargs = {
            'doc_ids': docids,
            'docs'   : invoice,
            'config' : config,
            'report' : report,
        }
        return docargs
