# noinspection PyStatementEffect
{
    'name'          : "Localization for Paraguay",
    'version'       : '0.2.3',
    'summary'       : 'Localization for Paraguay',
    'description'   : """Estructura básica necesaria para cualquier empresa de Paraguay, utilice o no Facturación Electrónica.
Conceptos Implementados
=======================
* Actividades Económicas (res.company.activity)
* Distritos (res.district)
* Localidades (res.location)
* Barrios (res.neighborhood)

Adaptaciones
============
* Paises.    - Código ISO 3166-3
* Contactos. - Campos de Distrito, Ciudad, Barrio
             - Naturaleza.
             - Tipo de Contacto
             - Tipo de Persona                 
""",
    'author'        : "Martin Salcedo Pacheco",
    'website'       : 'http://www.gadolconsulting.com',
    'depends'       : ['base',
                       'contacts',
                       'account',
                       'sale',
                       'stock',
                       'l10n_latam_base',
                       ],
    'category'      : 'Accounting/Localizations/Account Charts',
    'sequence'      : 10,
    'countries'     : ['py'],
    'demo'          : [

    ],
    'data'          : [
        'data/l10n_latam_identification_type.xml',
        'data/ir.ui.menu.csv',
        'data/ir_actions_server.xml',

        'data/res_country_state.xml',
        'data/res_district.xml',
        'data/res_location.xml',
        'data/res_neighborhood.xml',
        'data/res_company_activity.xml',
        'data/res_country.xml',
        'data/ir_cron.xml',

        'data/account_tax_group.xml',
        'data/account_tax_sales.xml',
        'data/account_tax_purchase.xml',

        'views/account_move.xml',
        'views/res_partner.xml',
        'views/res_partner_address.xml',
        'views/account_tax.xml',
        'views/ir_sequence.xml',
        'views/l10n_latam_identification_type.xml',
        'views/res_company.xml',
        'views/res_company_activity.xml',
        'views/res_config_settings_views.xml',
        'views/res_country.xml',
        'views/res_country_state.xml',
        'views/res_district.xml',
        'views/res_location.xml',
        'views/res_neighborhood.xml',
        'views/tax_payer.xml',
        'views/res_currency.xml',
        'views/res_currency_rate.xml',

        'wizard/tax_payer_process.xml',

        'security/ir_module_category.xml',
        'security/res_groups.xml',
        'security/ir_model_access.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',

    ],
    'application'   : False,
    'installable'   : True,
    'auto_install'  : False,
    'post_init_hook': '_l10n_py_updates',
    'assets'        : {},
    'license'       : 'LGPL-3',
}
