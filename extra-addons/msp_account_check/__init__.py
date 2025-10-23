from . import wizard
from . import models
from . import report

from odoo import api, SUPERUSER_ID


def _post_init_hook(env):
    env['account.check'].sudo()._create_third_sequences()
    env['account.check']._create_own_sequences()
    env['account.securities.deposit']._create_sequences()


def _uninstall_hook(env):
    seq_list = env['ir.sequence'].sudo().search(
            [
                ('code', 'in', ['account.check.own', 'account.check.third', 'account.securities.deposit'])
            ]
    )
    for seq in seq_list:
        seq.sudo().unlink()
    # pass
