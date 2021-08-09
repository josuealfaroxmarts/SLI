# -*- coding: utf-8 -*-
{
    "name": "Connection API Fletex",
    "summary": """Sistema de sincronizacion de API Fletex con Odoo""",
    "description": """Sistema de sincronizacion de API Fletex con Odoo""",
    "author": "[Xmarts] daniel.parra@xmarts.com",
    "website": "http://www.xmarts.com",
    "category": "Uncategorized",
    "version": "14.0.1.0.0",
    "depends": ["sli_trafitec"],
    "data": [
        "security/ir.model.access.csv",
        "data/fletex_api_config_data.xml",
        "data/automatic_api.xml",
        "views/fleet_vehicle_views.xml",
        "views/info_sync_fletex_views.xml",
        "views/res_partner_views.xml",
        "views/sync_info_views.xml",
    ]
}