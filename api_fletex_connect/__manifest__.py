# -*- coding: utf-8 -*-
{
    'name': "Connection API Fletex",

    'summary': """
        Sistema de sincronizacion de API Fletex con Odoo""",

    'description': """
        Sistema de sincronizacion de API Fletex con Odoo
    """,

    'author': "Xmarts",
    'website': "http://www.xmarts.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '10.0.1',

    # any module necessary for this one to work correctly
    'depends': ['sli_trafitec'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/fleet_vehicles_views.xml',
        'views/sync_info_views.xml',
        'data/fletex_api_config_data.xml',
        'data/automatic_api.xml'
    ]
}