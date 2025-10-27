# noinspection PyStatementEffect
{
    'name'        : "Localization for Paraguay",
    'version'     : '0.1',
    'summary'     : 'Localization for Paraguay',
    'description' : """Purchase stock localization for Paraguay""",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'http://www.gadolconsulting.com',
    'depends'     : [
        'l10n_py',
        'purchase_stock',
    ],
    'category'    : 'customizations',
    'sequence'    : 10,
    'countries'   : ['py'],
    'demo'        : [

    ],
    'data'        : [
        # 'data/l10n_latam_identification_type.xml',
        # 'data/ir.ui.menu.csv',
        # 'data/ir_actions_server.xml',

        # 'data/res_country_state.xml',
        # 'data/res_district.xml',
        # 'data/res_location.xml',
        # 'data/res_neighborhood.xml',
        # 'data/res_company_activity.xml',
        # 'data/res_country.xml',
        # 'data/ir_cron.xml',

        # 'data/account_tax_group.xml',
        # 'data/account_tax_sales.xml',
        # 'data/account_tax_purchase.xml',

        # 'views/account_move.xml',
        # 'views/res_partner.xml',
        # 'views/res_partner_address.xml',
        # 'views/account_tax.xml',
        # 'views/ir_sequence.xml',
        # 'views/l10n_latam_identification_type.xml',
        # 'views/res_company.xml',
        # 'views/res_company_activity.xml',
        # 'views/res_config_settings_views.xml',
        # 'views/res_country.xml',
        # 'views/res_country_state.xml',
        # 'views/res_district.xml',
        # 'views/res_location.xml',
        # 'views/res_neighborhood.xml',
        # 'views/tax_payer.xml',
        # 'views/res_currency.xml',
        # 'views/res_currency_rate.xml',
        # 'views/purchase_order.xml',
        'views/stock_valuation_layer.xml',
        'views/stock_picking.xml',

        # 'wizard/tax_payer_process.xml',

        # 'security/ir_module_category.xml',
        # 'security/res_groups.xml',
        # 'security/ir_model_access.xml',

        # 'entries/module_actions_act_window.xml',
        # 'entries/module_menu.xml',

    ],
    'application' : False,
    'installable' : True,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
