from . import models
from . import wizard
from odoo import api, SUPERUSER_ID


def _msp_account_branch_post_init_hook(env):
    moves = env['account.move'].with_context(prefetch_fields=False).search([])
    default_branch = env.company.get_default_branch()
    moves.write({'branch_id': default_branch.id})

    branchs = env['res.branch'].search([], order="id")
    if branchs:
        branchs.write({'establishment': '001'})
