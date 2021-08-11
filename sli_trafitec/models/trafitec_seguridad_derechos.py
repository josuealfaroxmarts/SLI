# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecSeguridadDerechos(models.Model):
	_name = 'trafitec.seguridad.derechos'
	_description = 'Seguridad derechos'
	
	name = fields.Char(
		string='Nombre', 
		required=True
	)
	detalles = fields.Char(
		string='Detalles', 
		required=True
	)