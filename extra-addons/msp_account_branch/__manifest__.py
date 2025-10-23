{
    'name'          : 'MSP Account + Branch',
    'version'       : '0.1',
    'summary'       : 'Customizations to Account + Branch',
    'description'   : "",
    'author'        : "Martin Salcedo Pacheco",
    'website'       : 'https://www.gadolconsulting.com/',
    'depends'       : [
        'msp_account',
        'msp_branch',
        'l10n_py_edi',
    ],
    'category'      : 'Customizations',
    'sequence'      : 22,
    'demo'          : [

    ],
    'data'          : [

        'security/ir_model_access.xml',

        'views/account_move.xml',
        'views/res_branch.xml',

    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,
    # 'pre_init_hook': 'pre_init_hook',
    'post_init_hook': '_msp_account_branch_post_init_hook',
    'assets'        : {},
    'license'       : 'LGPL-3',
}
