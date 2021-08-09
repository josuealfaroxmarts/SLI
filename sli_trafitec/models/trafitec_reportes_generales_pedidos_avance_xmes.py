# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecReportesGeneralesPedidosAvanceResultadoXMes(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.xmes'
	_description = 'Reportes generales pedidos avance xmes'
	
	buscar_id = fields.Many2one(
		string='Buscar',
		comodel_name='trafitec.reportes.generales.pedidos.avance.buscar'
	)
	cotizacion = fields.Char(string='Cotizacion', default='')
	cliente = fields.Char(string='Cliente', default='')
	ano = fields.Integer(string='Año', default=0)
	mes = fields.Integer(string='Mes', default='')
	viajes = fields.Integer(string='Viajes', default='')
	peso = fields.Float(string='Peso', default=0)