# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TrafitecCargosPendientes(models.TransientModel):
	_name = 'trafitec.cargospendientes'
	_description ='Cargos pendientes'

	descuento_id = fields.Integer(
		string='Id descuento', 
		default=0
	)
	contrarecibo_id = fields.Many2one(
		string='Contra recibo', 
		comodel_name='trafitec.contrarecibo'
	)
	detalles = fields.Char(string='Detalles')
	tipo = fields.Selection(
		[
			('commision', 'Comision'), 
			('discount', 'Descuento')
		], 
		string='Tipo'
	)
	total = fields.Float(
		string='Total', 
		default=0
	)
	abonos = fields.Float(
		string='Abonos', 
		default=0
	)
	saldo = fields.Float(
		string='Saldo', 
		default=0
	)
	