# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecSeguridadDerechosPerfil(models.Model):
	_name = 'trafitec.seguridad.derechos.perfil'
	_description = 'Seguridad derechos perfil'
	
	perfil = fields.Many2one(
		string='Perfil',
		comodel_name='trafitec.seguridad.perfiles'
	)
	derecho = fields.Many2one(
		string='Derecho',
		comodel_name='trafitec.seguridad.derechos',
		required=True
	)
	permitir = fields.Boolean(
		string='Permitir', 
		default=True
	)