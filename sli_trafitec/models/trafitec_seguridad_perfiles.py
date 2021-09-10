# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecSeguridadPerfiles(models.Model):
	_name = "trafitec.seguridad.perfiles"
	_description = "Seguridad Perfiles"

	name = fields.Char(
		string="Nombre", 
		default="", 
		required=True
	)
	detalles = fields.Char(
		string="Detalles", 
		default=""
	)
	derechos = fields.One2many(
		string="Derechos",
		comodel_name="trafitec.seguridad.derechos.perfil",
		inverse_name="perfil"
	)
	usuarios = fields.Many2many(
		string="Usuarios", 
		comodel_name="res.users"
	)
	state = fields.Boolean(
		string="Activo", 
		default=True
	)