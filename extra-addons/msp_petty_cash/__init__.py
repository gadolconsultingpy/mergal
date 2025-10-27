from . import models
from . import report
from . import wizard
from odoo import api, SUPERUSER_ID


def _post_init_hook(env):
    env['petty.cash.sheet'].sudo()._create_sequences()


def _uninstall_hook(env):
    seq_list = env['ir.sequence'].sudo().search(
            [
                ('code', '=', 'petty.cash.sheet')
            ]
    )
    for seq in seq_list:
        seq.sudo().unlink()
