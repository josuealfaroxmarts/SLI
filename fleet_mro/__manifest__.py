# -*- encoding: utf-8 -*-


{   
    "name"      : "Fleet Maintenance Repair & Overhauling (MRO) Management",
    "version"   : "1.0",
    "category"  : "Vertical",
    'complexity': "complex",
    "author"    : "Argil Consulting",
    "website"   : "http://www.argil.mx",
    "depends"   : ["fleet", "product", "operating_unit", "stock_operating_unit", "purchase","sale","hr"],
    "description": """
Fleet Maintenance Repair & Overhauling (MRO) Management
=======================================================

This application allows you to manage Fleet Maintenance Workshop (internal or open to the public), 
very useful when Compnay has its own Maintenance Workshop. 

It handles full Maintenance Workflow:
Opening Maintenance Order => Warehouse Integration => Closing Maintenance Order

Also, you can manage:
- Several Workshops
- Preventive Maintenance Cycles
- Corrective Maintenance
- Warehouse Integration for spare parts


""",
    "data" : [
                'security/fleet_mro_security.xml',
                'security/ir.model.access.csv',
                'views/ir_config_parameter.xml',
                'views/hr_employee_view.xml',
                'views/product_view.xml',
                'views/fleet_mro_base_view.xml',
                'views/operating_unit_view.xml',
                'views/fleet_vehicle_view.xml',
                'views/fleet_mro_order_view.xml',
                'views/fleet_mro_driver_report_view.xml',
                'views/fleet_mro_order_task_view.xml',
                'views/fleet_mro_order_task_time_view.xml',
                'views/fleet_mro_order_task_time_time_view.xml',
                'views/fleet_mro_order_task_spares_quotation_view.xml',
                'views/stock_view.xml',
                'views/purchase_order_view.xml',
                'report/mro_reports_template.xml',
                'report/mro_order_summary_report.xml',
                'report/mro_order_detail_report.xml',
                'report/mro_order_quotation_report.xml',
                'report/mro_order_final_quotation_report.xml',
                'report/mro_reports.xml',
                'views/fleet_mro_order_analisys_view.xml',
                
                   ], 
    'application': True,
    'installable': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

