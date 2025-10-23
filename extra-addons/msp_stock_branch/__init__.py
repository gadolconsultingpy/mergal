from . import models
from . import wizard
from odoo import api, SUPERUSER_ID


def _msp_stock_branch_post_init_hook(env):
    moves = env['stock.picking'].with_context(prefetch_fields=False).search([])
    default_branch = env.company.get_default_branch()
    moves.write({'branch_id': default_branch.id})
