from odoo import api, models, fields


class GenericMessageBox(models.TransientModel):
    _name = 'generic.message.box'
    _description = "Generic Message Box"

    title = fields.Char("Title")
    message_text = fields.Text("Message")

    @api.model
    def message(self, title, message):
        message = self.env['generic.message.box'].create({'title': title, 'message_text': message})
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : title,
            'res_model': 'generic.message.box',
            'view_mode': 'form',
            'view_id'  : self.env.ref('l10n_py_base.generic_message_box_form_view').id,
            'target'   : 'new',
            'res_id'   : message.id
        }
