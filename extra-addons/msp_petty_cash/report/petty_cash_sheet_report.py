from odoo import api, models, fields, _


class PettyCashSheetReport(models.AbstractModel):
    _name = 'report.msp_petty_cash.petty_cash_sheet_report'
    _description = 'Petty Cash Sheet Report'

    def _get_report_values(self, docids, data={}):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('msp_petty_cash.petty_cash_sheet_report')

        docs = self.env['petty.cash.sheet'].browse(docids)

        docargs = {
            'doc_ids'  : docids,
            'doc_model': report.model,
            'docs'     : docs,
            'report'   : report,
        }
        return docargs
