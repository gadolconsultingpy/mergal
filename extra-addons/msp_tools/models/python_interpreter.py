from odoo import api, fields, models, _
import logging
import sys
from io import StringIO
from odoo.exceptions import UserError
import traceback

_logger = logging.getLogger(__name__)

interpreter_path = "/mnt/interpreter"


class PythonInterpreter(models.Model):
    _name = 'python.interpreter'
    _description = 'Python Interpreter'
    _order = "favorite desc, use_ratio "

    name = fields.Char("Name")
    code = fields.Text('Python Code')
    result = fields.Text('Result')
    console_output = fields.Selection(
            [
                ('console', 'Console'),
                ('screen', 'Screen'),
                ('both', 'Both')
            ], default='both', string="Console Output"
    )
    filename = fields.Many2one('python.filename', string="Filename")
    hide_code = fields.Boolean("Hide Code", default=False)
    favorite = fields.Selection(
            [
                ('0', 'normal'),
                ('1', 'favorite')
            ], string="Favorite", default="0"
    )
    use_ratio = fields.Integer("Use Ratio", default=0)
    code_preview = fields.Text("Code Preview", compute="_compute_code_preview")

    @api.onchange('name')
    def _onchange_name_blank(self):
        self.filename = None

    @api.depends('code')
    def _compute_code_preview(self):
        for rec in self:
            if rec.code:
                rec.code_preview = "\n".join(rec.code.split("\n")[:5])
            else:
                rec.code_preview = ""

    def load_and_execute(self):
        if self.filename:
            fileobj = open("%s/%s" % (interpreter_path, self.filename.name), 'r')
            self.code = "".join(fileobj.readlines())
            fileobj.close()
            self.execute()

    def execute(self, objects={}):
        _logger.info("Executing: %s" % (self.name))
        _logger.info("Parameters: %s" % (objects))
        self.use_ratio += 1
        if not self.filename:
            filename = self.name.strip().lower().replace(" ", "_")
            self.filename = self.filename.create_filename(filename)
        if self.code:
            try:
                fileobj = open("%s/%s" % (interpreter_path, self.filename.name), 'w')
                fileobj.write(self.code)
                fileobj.close()
            except Exception as e:
                msg = _("Error writing file: %s") % e
                _logger.error(msg)
            lcs = locals()
            lcs['self'] = self
            lcs['_logger'] = _logger
            lcs.update(objects)

            try:
                old_stdout = sys.stdout
                redirected_output = sys.stdout = StringIO()
                exec(self.code, globals(), lcs)
                sys.stdout = old_stdout
                python_out = redirected_output.getvalue()
                if self.console_output in ['screen', 'both']:
                    self.result = python_out
                if self.console_output in ['console', 'both']:
                    print(python_out)
            except SyntaxError as err:
                error_class = err.__class__.__name__
                detail = err.args[0]
                line_number = err.lineno
                raise UserError(
                        "%s en linea %d del siguiente código  \n%s: %s" % (error_class, line_number, self.code, detail))

    def refresh_filename(self):
        import os
        filename = self.env['python.filename'].search([])
        filename.unlink()
        for dirpath, names, files in os.walk(interpreter_path):
            for ff in files:
                if ff.endswith(".py"):
                    self.env['python.filename'].create({'name': ff})

    def copy(self, default=None):
        record = super(PythonInterpreter, self).copy(default=default)
        for rec in record:
            rec.name = "%s %s" % (rec.name, _("(copy)"))
        return record


class PythonInterpreterFilename(models.Model):
    _name = 'python.filename'
    _description = 'Python Filename'

    name = fields.Char("Name")

    @api.model
    def create_filename(self, name):
        return self.env[self._name].create({'name': "%s.py" % (name)})
