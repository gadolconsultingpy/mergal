from odoo import api, models, fields, _


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    issue_reason_id = fields.Many2one('edi.issue.reason', string="Select a Reason", required=True)
    invoice_payment_term_id = fields.Many2one('account.payment.term', string="Payment Term")

    @api.model
    def default_get(self, fields):
        vals = super(AccountMoveReversal, self).default_get(fields)
        reversal_journal = self.env['account.journal'].search(
                [
                    ('invoice_type_id.code', '=', '5')
                ], order="sequence", limit=1)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
                'active_model') == 'account.move' else self.env['account.move']
        payment_term_id = [x.invoice_payment_term_id.id for x in move_ids][0]
        vals['journal_id'] = reversal_journal.id if reversal_journal else False
        vals['invoice_payment_term_id'] = payment_term_id if payment_term_id else self.env[
            'account.payment.term'].search([], order="sequence", limit=1)
        return vals

    def _prepare_default_reversal(self, move):
        vals = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        vals['issue_reason_id'] = self.issue_reason_id.id
        vals['invoice_payment_term_id'] = self.invoice_payment_term_id.id
        vals['reversal_reason'] = self.reason
        # vals['transaction_type_id'] = move._default_transaction_type()
        # vals['tax_type_id'] = move._default_tax_type()
        # vals['presence_id'] = move._default_presence_id()
        # reverted_invoice_ids
        if move.control_code and move.sequence_id:
            rvals = {}
            rvals["reversion_document_type"] = "1"
            rvals["reverted_cdc"] = move.control_code
            vals['reverted_invoice_ids'] = [(0, 0, rvals)]
        else:
            rvals = {}
            rvals["reversion_document_type"] = "2"
            rvals["reverted_stamped_number"] = move.timbrado_id.name
            rvals["reverted_invoice_establishment"] = move.name.split("-")[0]
            rvals["reverted_invoice_dispatch_point"] = move.name.split("-")[1]
            rvals["reverted_invoice_number"] = move.name.split("-")[2]
            rvals["reverted_invoice_date"] = move.invoice_date
            vals['reverted_invoice_ids'] = [(0, 0, rvals)]
        return vals
