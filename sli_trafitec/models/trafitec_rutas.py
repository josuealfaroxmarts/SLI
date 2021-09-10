# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64

	
class TrafitecRutas(models.Model):
	_name = "trafitec.rutas"
	_description = "Rutas"

	asociado = fields.Many2one(
		"res.partner", 
		string="Asociado"
	)
	estado = fields.Many2one(
		"res.country.state", 
		string="Estado", 
		domain=[
			("country_id", "=", 157)
		], 
		required=True
	)
	vigente = fields.Boolean(string="Vigente")
