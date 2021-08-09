# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import xlrd
import shutil
import datetime
import logging
# from odoo.tools import amount_to_text
from . import amount_to_text
import xlsxwriter
import base64
# from amount_to_text import *
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

_logger = logging.getLogger(__name__)


class TrafitecProgramacionPagosXFacturasBuscar(models.TransientModel):
	_name = 'trafitec.programacionpagosx.facturas.buscar'
	_description='programacion pagox facturas buscar'

	programacionpagos_id = fields.Many2one(
		string='Programacion de pagos', 
		comodel_name='trafitec.programacionpagosx'
	)
	factura_id = fields.Many2one(
		string='Factura', 
		comodel_name='account.move', 
		domain=[
			('state', '=', 'open'), 
			('type', '=', 'in_invoice')
		]
	)
	fecha = fields.Date(
		string='Fecha', 
		related='factura_id.date'
	)
	persona_id = fields.Many2one(
		string='Persona', 
		related='factura_id.partner_id'
	)
	moneda_id = fields.Many2one(
		string='Moneda', 
		related='factura_id.currency_id'
	)
	total = fields.Monetary(
		string='Total', 
		related='factura_id.amount_total', 
		currency_field='moneda_id'
	)
	saldo = fields.Monetary(
		string='Saldo', 
		related='factura_id.amount_residual', 
		currency_field='moneda_id'
	)
	