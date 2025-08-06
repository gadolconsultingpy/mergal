# noinspection PyStatementEffect
{
    'name'        : "Localization for Paraguay - CoA",
    'version'     : '0.1',
    'summary'     : 'Localization for Paraguay - Chart of Accounts',
    'description' : """Plan de Cuentas Paraguay""",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'https://www.gadolconsulting.com/',
    'category'    : 'Accounting/Localizations/Account Charts',
    'sequence'    : 10,
    'countries'   : ['py'],
    'depends'     : ['base',
                     'account',
                     ],
    'demo'        : [

    ],
    'data'        : [
        'data/account_account_tag.xml',
        'data/account_tax_group.xml',

    ],
    'assets'      : {},
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'license'     : 'LGPL-3',
}
