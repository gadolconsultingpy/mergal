# noinspection PyStatementEffect
{
    'name'        : "Localization for Paraguay - RG 90/2021",
    'version'     : '0.1.1',
    'summary'     : 'Localization for Paraguay - RG 90/2021',
    'description' : """Electronic Registry of Sales and Purchases (RG 90/2021)""",
    'author'      : "Gadol Consulting",
    'website'     : 'http://www.gadolconsulting.com',
    'depends'     : [
        'account',
        'l10n_py',
        'l10n_py_base',
    ],
    'category'    : 'Accounting/Localizations',
    'sequence'    : 10,
    'countries'   : ['py'],
    'demo'        : [

    ],
    'data'        : [
        'security/ir_model_access.xml',

        'data/account_document_type.xml',

        'views/account_document_type.xml',
        'views/res_partner_stamped.xml',
        'views/account_move.xml',
        'views/res_config_custom.xml',

        # 'wizard/tax_payer_process.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',

    ],
    'application' : False,
    'installable' : True,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
