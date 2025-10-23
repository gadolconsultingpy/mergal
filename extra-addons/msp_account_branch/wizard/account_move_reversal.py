from odoo import api, models, fields, _


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        vals = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        vals['branch_id'] = move.invoice_user_id.branch_id.id
        return vals

    def reverse_moves(self, is_modify=False):
        action = super(AccountMoveReversal, self).reverse_moves(is_modify=is_modify)
        res_id = action.get('res_id')
        credit_note = self.env['account.move'].browse(res_id)
        sequence_id = credit_note._search_sequence_id(user_id=credit_note.invoice_user_id.id,
                                                      move_type='out_refund')
        credit_note.write({'sequence_id': sequence_id})
        return action
