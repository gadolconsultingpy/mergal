import logging
import jinja2
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPrintingFormat(models.Model):
    _name = 'res.printing.format'
    _description = 'Printing Format'

    @api.model
    def _selection_target_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    name = fields.Char("Name")
    model_id = fields.Many2one('ir.model', string="Model")
    header = fields.Html("Header")
    header_preview = fields.Html("Header Preview")
    header_raw = fields.Text("Raw Header")
    footer_preview = fields.Html("Footer Preview")
    footer = fields.Html("Footer")
    footer_raw = fields.Text("Raw Footer")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    lang_option = fields.Selection(
            [
                ('partner', 'Partner'),
                ('company', 'Company'),
                ('specific', 'Specific'),
            ], string="Language Option", default='partner'
    )
    lang = fields.Many2one('res.lang', string="Language")
    label_ids = fields.One2many('res.printing.format.label', 'parent_id', string="Labels")
    resource_ref = fields.Reference(
            string='Record',
            compute='_compute_resource_ref',
            compute_sudo=False, readonly=False,
            selection='_selection_target_model',
            store=True
    )
    no_record = fields.Boolean('No Record', compute='_compute_no_record')

    def make_header(self):
        if self.header_raw:
            self.header = self.header_raw

    def sync_header(self):
        if self.header:
            self.header_raw = self.header

    def preview_header(self):
        if self.header:
            env = jinja2.Environment()
            for preview, preview_sudo in zip(self, self.sudo()):
                if preview_sudo.resource_ref:
                    kwargs = {'record': preview_sudo.resource_ref}
                    if preview_sudo.header:
                        try:
                            preview.header_preview = env.from_string(preview_sudo.header).render(kwargs)
                        except BaseException as errstr:
                            preview.header_preview = preview_sudo.header
                            _logger.error(f"Error rendering header: {errstr}")

                    else:
                        preview.header_preview = "<html><body>No header</body></html>"
                else:
                    preview.header_preview = self.header

    def make_footer(self):
        if self.footer_raw:
            self.footer = self.footer_raw

    def sync_footer(self):
        if self.footer:
            self.footer_raw = self.footer

    def preview_footer(self):
        env = jinja2.Environment()
        for preview, preview_sudo in zip(self, self.sudo()):
            if preview_sudo.resource_ref:
                kwargs = {'record': preview_sudo.resource_ref}
                if preview_sudo.footer:
                    try:
                        preview.footer_preview = env.from_string(preview_sudo.footer).render(kwargs)
                    except BaseException as errstr:
                        preview.footer_preview = preview_sudo.footer
                        _logger.error(f"Error rendering footer: {errstr}")
                else:
                    preview.footer_preview = "<html><body>No footer</body></html>"
            else:
                preview.footer_preview = self.footer

    def search_resource_ref(self):
        """
        This method is used to search for a record based on the resource_ref field.
        It splits the resource_ref into model and id, and then searches for the record.
        """
        for preview in self:
            preview._compute_resource_ref()
        return False

    @api.depends('resource_ref', 'model_id', 'header_raw')
    def _compute_header_preview(self):
        env = jinja2.Environment()
        for preview, preview_sudo in zip(self, self.sudo()):
            if preview_sudo.resource_ref:
                kwargs = {'record': preview_sudo.resource_ref}
                if preview_sudo.header:
                    try:
                        preview.header_preview = env.from_string(preview_sudo.header).render(kwargs)
                    except BaseException as errstr:
                        preview.header_preview = preview_sudo.header
                        _logger.error(f"Error rendering header: {errstr}")

                else:
                    preview.header_preview = "<html><body>No header</body></html>"
            else:
                preview.header_preview = self.header

    @api.depends('resource_ref', 'model_id', 'footer_raw')
    def _compute_footer_preview(self):
        env = jinja2.Environment()
        for preview, preview_sudo in zip(self, self.sudo()):
            if preview_sudo.resource_ref:
                kwargs = {'record': preview_sudo.resource_ref}
                if preview_sudo.footer:
                    preview.footer_preview = env.from_string(preview_sudo.footer).render(kwargs)
                else:
                    preview.footer_preview = "<html><body>No footer</body></html>"
            else:
                preview.footer_preview = self.footer

    @api.depends('model_id')
    def _compute_no_record(self):
        for preview, preview_sudo in zip(self, self.sudo()):
            model_id = preview_sudo.model_id
            preview.no_record = not model_id or not self.env[model_id.model].search_count([])

    @api.depends('model_id')
    def _compute_resource_ref(self):
        for preview in self:
            model = self.model_id.model
            try:
                res = self.env[model].search([], limit=1)
                print("res", res)
                preview.resource_ref = f'{model},{res.id}' if res else False
            except BaseException as errstr:
                preview.resource_ref = False

    # @api.onchange('header', 'header_preview')
    # def _onchange_header(self):
    #     if self.no_record:
    #         self.header_raw = self.header
    #     else:
    #         self.header_raw = self.header_preview

    # @api.onchange('footer', 'footer_preview')
    # def _onchange_footer(self):
    #     if self.no_record:
    #         self.footer_raw = self.footer
    #     else:
    #         self.footer_raw = self.footer_preview

    # @api.onchange('header_raw')
    # def _onchange_header_raw(self):
    #     self.header = self.header_raw

    # @api.onchange('footer_raw')
    # def _onchange_footer_raw(self):
    #     self.footer = self.footer_raw

    def get_label(self, label, **kwargs):
        env = jinja2.Environment()
        for label_id in self.label_ids:
            if label_id.name == label:
                return env.from_string(label_id.translation).render(kwargs)
        return label


class ResPrintingFormatLabel(models.Model):
    _name = 'res.printing.format.label'
    _description = 'Printing Format Label'

    name = fields.Char("Name")
    parent_id = fields.Many2one('res.printing.format', string="Parent")
    translation = fields.Char("Translation")
