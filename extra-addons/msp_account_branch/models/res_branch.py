from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ResBranch(models.Model):
    _inherit = 'res.branch'

    establishment = fields.Char('Establishment Code', size=3)
    dispatch_point_ids = fields.One2many('res.branch.dispatch.point', 'parent_id', string="Dispatch Point")
    set_default_journal = fields.Boolean("Use Default Journal")
    sequence_by_salesman = fields.Boolean('Sequence by Salesman')

    def get_dispatch_point(self, **kwargs):
        for dp in sorted(self.dispatch_point_ids, key=lambda x: x.sequence):
            salesman_id = kwargs.get('salesman_id', -1)
            move_type = kwargs.get('move_type', "")
            if self.sequence_by_salesman:
                if dp.salesman_id and salesman_id != dp.salesman_id.id:
                    continue
            if dp.move_type and move_type != dp.move_type:
                continue
            return dp
        return None

    def get_prefix_sequence(self, **kwargs):
        prefix = kwargs.get("prefix")
        move_type = kwargs.get("move_type")
        for dp in sorted(self.dispatch_point_ids, key=lambda x: x.sequence):
            if dp.sequence_id.prefix == prefix and dp.move_type == move_type:
                return dp.sequence_id
        error_msg = "Falta Secuencia para el Prefijo: [%s]" % (prefix)
        raise UserError(error_msg)

    def get_prefix_dispatch_point(self, **kwargs):
        prefix = kwargs.get("prefix")
        move_type = kwargs.get("move_type")
        for dp in sorted(self.dispatch_point_ids, key=lambda x: x.sequence):
            if dp.sequence_id.prefix == prefix and dp.move_type == move_type:
                return dp
        error_msg = "Falta Secuencia para el Prefijo: [%s]" % (prefix)
        raise UserError(error_msg)


class ResBranchDispatchPoint(models.Model):
    _name = 'res.branch.dispatch.point'
    _description = 'Dispatch Point'

    parent_id = fields.Many2one('res.branch', string="Branch", ondelete="cascade")
    sequence = fields.Integer('Sequence')
    dispatch_point = fields.Char("Dispatch Point", size=3, required=True)
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_type = fields.Selection(
            [
                ('out_invoice', 'Sale Invoice'),
                ('out_refund', 'Sale Credit Note'),
                ('out_receipt', 'Sale Receipt'),
            ], string="Move Type"
    )
    sequence_id = fields.Many2one('ir.sequence', string="Sequence Id")
    sequence_use = fields.Float('Use %', compute='_compute_sequence_use')
    sequence_next_actual = fields.Integer("Next Actual", related="sequence_id.number_next_actual")
    sequence_remain = fields.Integer("Remain", compute='_compute_sequence_use')
    salesman_id = fields.Many2one('res.users', string="Salesman")

    @api.depends('sequence_id.number_next')
    def _compute_sequence_use(self):
        for rec in self:
            if not rec.sequence_id:
                rec.sequence_use = 0
                rec.sequence_remain = 0
            else:
                from_number = 1
                to_number = int("9" * rec.sequence_id.padding or 7)
                numbers = to_number - from_number + 1
                rec.sequence_use = (rec.sequence_id.number_next_actual + 1 - from_number) * 100 / numbers
                rec.sequence_remain = to_number - rec.sequence_id.number_next_actual + 1

    def next_sequence(self, cur_seq):
        a, b = ord(cur_seq[0]), ord(cur_seq[1])
        b = b + 1
        if b == 91:
            a = a + 1
            b = 65
        return "%s%s" % (chr(a), chr(b))

    def action_create_sequence(self):
        svars = {}
        code = 'account.move.%s.%s' % (self.parent_id.establishment, self.dispatch_point)
        svars["code"] = code
        last_seq = self.env['ir.sequence'].search(
                [
                    ('code', '=', code),
                    ('journal_id', '=', self.journal_id.id)
                ], order='create_date desc', limit=1)
        code_char_ord = ""
        if last_seq:
            print(last_seq[0].prefix.split("-"))
            if len(last_seq[0].prefix.split("-")) == 3:
                code_char_ord = "AA"
            if len(last_seq[0].prefix.split("-")) == 4:
                print(last_seq[0].prefix.split("-")[0])
                code_char_ord = last_seq[0].prefix.split("-")[0]
                code_char_ord = self.next_sequence(code_char_ord)
        if code_char_ord:
            prefix = "%s-%s-%s-" % (code_char_ord, self.parent_id.establishment, self.dispatch_point)
        else:
            prefix = "%s-%s-" % (self.parent_id.establishment, self.dispatch_point)

        svars["prefix"] = prefix
        svars["name"] = "%s %s" % (self.journal_id.name, prefix[:-1])
        svars["establishment"] = self.parent_id.establishment
        svars["dispatch_point"] = self.dispatch_point
        svars["padding"] = 7
        svars["binding_model_id"] = self.env.ref('account.model_account_move').id
        svars["from_number"] = 1
        svars["to_number"] = 9999999
        svars["journal_id"] = self.journal_id.id
        seq = self.env['ir.sequence'].create(svars)
        if seq:
            self.sequence_id = seq.id
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : 'Invoices Sequence',
            'res_model': 'ir.sequence',
            'view_mode': 'form',
            'view_id'  : self.env.ref('base.sequence_view').id,
            'target'   : 'new',
            'res_id'   : seq.id
        }
