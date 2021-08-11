# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64

	
class TrafitecUnidades(models.Model):
	_name = 'trafitec.unidades'
	_description ='unidades'

	asociado = fields.Many2one(
		'res.partner', 
		string='Asociado'
	)
	movil = fields.Many2one(
		'trafitec.moviles', 
		string='Móvil', 
		required=True
	)
	cantidad = fields.Integer(
		string='Cantidad', 
		required=True
	)
