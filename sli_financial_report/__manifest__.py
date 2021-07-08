# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

{
	'name': 'Reportes Financieros SLI',
	'version': '10.0.0',
	'summary': 'Reporte financieros',
	'category': 'Account',
	'depends': ['base', 'account'],
	'website': '',
	'author': 'Soluciones Logísticas Inteligentes SA de CV, Developer: Ing. Viridiana Cruz Santos',

	'data': [
		'security/ir.model.access.csv',
		'views/menu_main_view.xml',
		'views/supplier_invoice_view.xml',
		'views/purchase_report_view.xml',
		'views/supplier_payment_term_view.xml',
		'views/download_attachment_view.xml',
		# 'inherits/views/account_invoice_view.xml',
	],
	'demo': [],
	'qweb': [],

	'installable': True,
	'auto_install': False,
}