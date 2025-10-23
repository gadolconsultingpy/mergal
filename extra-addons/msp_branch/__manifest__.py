{
    'name'          : 'MSP Branch',
    'version'       : '0.1.1',
    'summary'       : 'Establishement and dispatch point management',
    'description'   : "Concept of establishments and dispatch points",
    'author'        : "Martin Salcedo Pacheco",
    'website'       : 'https://www.gadolconsulting.com/',
    'depends'       : [
        'base',
        'l10n_py',
    ],
    'category'      : 'Customizations',
    'sequence'      : 21,
    'demo'          : [

    ],
    'data'          : [
        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',
        'security/ir_model_access.xml',

        'views/res_branch.xml',
        'views/res_partner.xml',
        'views/res_users.xml',

    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,
    # 'pre_init_hook': 'pre_init_hook',
    'post_init_hook': '_msp_branch_post_init_hook',
    'assets'        : {},
    'license'       : 'LGPL-3',
}
