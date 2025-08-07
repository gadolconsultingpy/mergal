import base64

from odoo import api, fields, models
from odoo.fields import Many2one, Many2oneReference, Boolean

class ModelExportXML(models.Model):
    _name = 'model.export.xml'
    _description = 'Export Model data to XML format'

    model_id = fields.Many2one('ir.model', string='Model')
    field_lines = fields.One2many('model.field.export.xml', 'parent_id', string="Fields")
    fileobject = fields.Binary("File")
    filename = fields.Char("Filename")
    noupdate = fields.Boolean('No Update', default=True)

    CORE_COLUMNS = models.MAGIC_COLUMNS
    CORE_COLUMNS.extend(['__last_update'])

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            model = self.env[self.model_id.model]
            self.field_lines = False
            self.field_lines = [(0,0,{'name':field}) for field in model._fields if field not in self.CORE_COLUMNS]
            self.filename = "%s.xml" %(self.model_id.model.replace(".","_"))
        else:
            self.field_lines = False

    def action_generate(self):
        data_struc = "<odoo>\n"
        data_struc += "    <data %s>\n" %("noupdate='1' " if self.noupdate else '')
        record_list = self.env[self.model_id.model].search([], order='id')
        for record in record_list:
            # print(record._model_fields)
            # print(dir(record))
            xml_id = record.get_external_id().get(record.id)
            if not xml_id:
                xml_id = record.export_data(['id']).get('datas')[0][0].replace("__export__.","")
                #print(xml_id)
            data_struc += "        <record id='%s' model='%s' >\n" %(xml_id, self.model_id.model)
            for field in self.field_lines:
                # print(["FIELDNAME", field.name, type(record[field.name])])
                # print(dir(record[field.name]))
                # if field.name == 'country_id':
                if isinstance(record._fields[field.name], Many2one):
                    data_struc += "            <field name='%s' ref='%s'/>\n" %(field.name, record[field.name].get_external_id().get(record[field.name].id) or '')
                else:
                    # print("IS BOOL", isinstance(record[field.name], bool))
                    if isinstance(record._fields[field.name], Boolean):
                        value = "True" if record[field.name] else "False"
                        data_struc += "            <field name='%s' eval='%s' />\n" % (field.name, value)
                    else:
                        value = record[field.name] or ''
                        if value:
                            data_struc += "            <field name='%s'>%s</field>\n" %(field.name, value)

            data_struc += "        </record>\n\n"
        data_struc += "    </data>\n"
        data_struc += "</odoo>\n"
        # print(data_struc)
        self.fileobject = base64.b64encode(data_struc.encode())
        # print(dir(record))
        # print(record.fields_get_keys())

class ModelFieldExportXML(models.Model):
    _name = 'model.field.export.xml'
    _description = 'Export Model field data to XML format'

    parent_id = fields.Many2one('model.export.xml')
    sequence = fields.Integer('Sequence')
    name = fields.Char('Name')
