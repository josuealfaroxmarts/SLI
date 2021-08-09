# -*- coding: utf-8 -*-

from odoo import api, fields, models


# Descuentos por cobrar
class TrafitecContrareciboDescuentosX(models.TransientModel):
	_name = 'trafitec.contrarecibos.descuentosx'
	_description = 'Contrarecibos descuentos'

	descuento_id = fields.Many2one(
		comodel_name='trafitec.descuentos', 
		string='Descuentos'
	)
	concepto = fields.Char(
		string='Concepto', 
		default=''
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
	abono = fields.Float(
		string='Abono', 
		default=0
	)
