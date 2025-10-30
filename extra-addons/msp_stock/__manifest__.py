{
    'name'        : 'MSP Stock',
    'version'     : '0.1',
    'summary'     : 'Customizations to Stock',
    'description' : """Additional Stock Features
=========================
Enable the Unit Of Measure Menu Entry
    """,
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'http://www.gadolconsulting.com',
    'depends'     : [
        'stock',
    ],
    'category'    : 'Customizations',
    'sequence'    : 60,
    'demo'        : [

    ],
    'data'        : [
        'entries/module_menu.xml',

        'views/stock_move.xml',
        'views/stock_picking_type.xml',

        'wizard/stock_move_select_lots.xml',

        'security/ir_model_access.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
