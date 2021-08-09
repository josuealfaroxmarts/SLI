# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class trafitec_viajes_scan(models.Model):
	_name = 'trafitec.viajes.scan'
	_description = 'viajes scan'
	
	viaje_id = fields.Many2one(
		string='Viaje',
		comodel_name='trafitec.viajes',
		required=True
	)
	st = fields.Selection([
			('not_started', 'No iniciado'),
			('started', 'Iniciado')
		],
		string='Estado'
	)