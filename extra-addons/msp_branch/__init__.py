from . import models
from odoo import api, SUPERUSER_ID


def _msp_branch_post_init_hook(env):
    companies = env['res.company'].search([])
    for comp in companies:
        vals = {}
        vals['company_id'] = comp.id
        vals['partner_id'] = comp.partner_id.id
        vals['name'] = comp.partner_id.name
        vals['code'] = comp.partner_id.id
        branch = env['res.branch'].create(vals)

        users = env['res.users'].search([])
        for user in users:
            user.write({'branch_id': branch.id})
