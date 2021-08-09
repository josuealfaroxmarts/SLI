# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecReportesGeneralesPedidosAvanceResultado(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.resultado'
	_description = 'Reportes generales pedidos avance resultado'
	buscar_id = fields.Many2one(
		string='Buscar',
		comodel_name='trafitec.reportes.generales.pedidos.avance.buscar'
	)
	cotizacion_folio = fields.Char(string='Cotizacion', default='')
	cotizacion_cliente = fields.Char(string='Cliente', default='')
	cotizacion_numeroviajes = fields.Float(
		string='No. de viajes',
		default=0,
		help='Numero de viajes.'
	)
	cotizacion_peso_actual = fields.Float(string='Peso actual')
	cotizacion_peso_total = fields.Float(string='Peso total')
	cotizacion_porcentaje = fields.Float(
		string='% Porcentaje de avance',
		default=0,
		help='Porcentaje de avance del la cotización.'
	)