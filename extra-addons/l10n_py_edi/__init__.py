from . import models
from . import wizard
from . import report


def _l10n_py_edi_updates(env):
    journals = env['account.journal'].search([])
    for jj in journals:
        if jj.code in ["NCE", "NDE"]:
            continue
        if jj.code == 'INV' and jj.type == 'sale':
            jj.write({'invoice_type_id': env.ref('l10n_py_edi.edi_document_type_1').id, 'code': 'FE'})
        else:
            jj.write({'invoice_type_id': env.ref('l10n_py_edi.edi_document_type_x').id})
