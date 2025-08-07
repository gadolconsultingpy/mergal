from . import models
from . import wizard
from odoo import api, SUPERUSER_ID


def _l10n_py_updates(env):
    pquery = "UPDATE res_partner SET street_name = street "
    env.cr.execute(pquery)
