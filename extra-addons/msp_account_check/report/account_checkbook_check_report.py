from num2words import num2words

from odoo import api, models, fields, _


class AccountCheckbookCheckReport(models.AbstractModel):
    _name = 'report.msp_account_check.account_checkbook_check_report'
    _description = "Account Checkbook Check Report"

    def _get_report_values(self, docids, data=None):
        report = self.get_report()
        checkbook = self.env['account.checkbook'].browse(docids)
        docs = self.env['account.check'].browse([x.check_id.id for x in checkbook.check_ids if not x.printed])
        docargs = {
            'doc_ids'  : docids,
            'doc_model': report.model,
            'docs'     : docs,
            'report'   : self,
            # 'format_value': docs.format_value,
        }
        for check in checkbook.check_ids:
            check.write({'printed': True})
            check.check_id.write({'state': 'issued'})
        return docargs

    def get_report(self):
        report_obj = self.env['ir.actions.report']
        return report_obj._get_report_from_name('msp_account_check.account_checkbook_check_report')

    @api.model
    def format_value(self, value):
        return "{:,.0f}".format(value).replace(",", ":").replace(".", ",").replace(":", ".")

    def num_to_words_es(self, numero):
        return num2words(numero, lang="es")


class AccountCheckbookContinentalWithStub(models.AbstractModel):
    _inherit = 'report.msp_account_check.account_checkbook_check_report'
    _name = 'report.msp_account_check.account_checkbook_continental'
    _description = "Checkbook Continental with Stub"

    def get_report(self):
        report_obj = self.env['ir.actions.report']
        return report_obj._get_report_from_name('msp_account_check.account_checkbook_continental')


class AccountCheckbookContinentalWithoutStub(models.AbstractModel):
    _inherit = 'report.msp_account_check.account_checkbook_check_report'
    _name = 'report.msp_account_check.account_checkbook_continental_stub'
    _description = "Checkbook Continental with Stub"

    def get_report(self):
        report_obj = self.env['ir.actions.report']
        return report_obj._get_report_from_name('msp_account_check.account_checkbook_continental_stub')
