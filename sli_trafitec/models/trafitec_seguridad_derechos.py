# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class trafitec_seguridad_derechos(models.Model):
	_name = 'trafitec.seguridad.derechos'
	_description = 'Seguridad derechos'
	
	name = fields.Char(string='Nombre', required=True)
	detalles = fields.Char(string='Detalles', required=True)