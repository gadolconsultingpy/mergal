from odoo import api, models, fields, _


class AccountPaymentReport(models.AbstractModel):
    _name = 'report.msp_account.account_payment_report'
    _description = 'Account Payment Report'

    def _get_report_values(self, docids, data={}):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('msp_account.account_payment_report')

        docs = self.env['account.payment'].browse(docids)

        docargs = {
            'doc_ids'  : docids,
            'doc_model': report.model,
            'docs'     : docs,
            'report'   : report,
        }
        return docargs
