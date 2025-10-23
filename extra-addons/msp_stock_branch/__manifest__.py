{
    'name'          : 'MSP Stock + Branch',
    'version'       : '0.1',
    'summary'       : 'Customizations to Stock + Branch',
    'description'   : "",
    'author'        : "Martin Salcedo Pacheco",
    'website'       : 'https://www.gadolconsulting.com/',
    'depends'       : [
        'stock',
        'msp_branch',
        'msp_account_branch',
    ],
    'category'      : 'Customizations',
    'sequence'      : 22,
    'demo'          : [

    ],
    'data'          : [

        # 'security/ir_model_access.xml',

        # 'views/account_move.xml',
        # 'views/stock_picking.xml',

    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,
    # 'pre_init_hook': 'pre_init_hook',
    'post_init_hook': '_msp_stock_branch_post_init_hook',
    'assets'        : {},
    'license'       : 'LGPL-3',
}
