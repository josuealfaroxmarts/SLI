# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecPresupuestos(models.Model):
	_name = 'trafitec.presupuestos'
	_description = 'presupuestos'
	
	ano = fields.Integer(string='Año', default=2018)
	monto_mes1 = fields.Float(string='Enero', default=0)
	monto_mes2 = fields.Float(string='Febrero', default=0)
	monto_mes3 = fields.Float(string='Marzo', default=0)
	monto_mes4 = fields.Float(string='Abril', default=0)
	monto_mes5 = fields.Float(string='Mayo', default=0)
	monto_mes6 = fields.Float(string='Junio', default=0)
	monto_mes7 = fields.Float(string='Julio', default=0)
	monto_mes8 = fields.Float(string='Agosto', default=0)
	monto_mes9 = fields.Float(string='Septiembre', default=0)
	monto_mes10 = fields.Float(string='Octubre', default=0)
	monto_mes11 = fields.Float(string='Noviembre', default=0)
	monto_mes12 = fields.Float(string='Diciembre', default=0)
	st = fields.Selection([
			('inactive', 'Inactivo'),
			('active', 'Activo')
		],
		string='Estado',
		default='active'
	)