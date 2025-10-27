from odoo import api, models, fields, _
import jinja2

class EDITemplate(models.Model):
    _name = 'edi.template'
    _description = 'EDI Template'
    _order = 'sequence'

    name = fields.Char("Name")
    template = fields.Text("Template")
    sequence = fields.Integer("Seq")

    @api.model
    def _render(self, template_name, **kwargs):
        template = self.env['edi.template'].search([('name','=',template_name)])
        env = jinja2.Environment()
        template = env.from_string(template.template)
        content = template.render(kwargs)
        # print(content)
        return content

    def test_template(self):
        env = jinja2.Environment()
        objects = {}
        objects['envelope_content'] = ""
        objects['rEnviEventoDe'] = "sadfasdf"
        objects['move'] = self.env['account.move'].search(
                [
                    ('move_type','=','out_invoice')
                ], limit=1, order="id desc"
        )
        template = env.from_string(self.template)
        content = template.render(objects)
        print(content)
