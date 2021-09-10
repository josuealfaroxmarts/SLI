# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecSucursal(models.Model):
	_name = "trafitec.sucursal"
	_description = "Sucursal"
	
	name = fields.Char(
		string="Nombre", 
		required=True
	)
	active = fields.Boolean(
		string="Activo", 
		default=True
	)

	_sql_constraints = [
		("name_uniq", "unique(name)", "El nombre no se puede repetir.")
	]