# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecTipodocumento(models.Model):
	_name = 'trafitec.tipodoc'
	_description ='tipo doc'

	name = fields.Char(
		string="Nombre", 
		required=True
	)
	tipo = fields.Selection(
		[
			('origen', 'Origen'), 
			('destino', 'Destino')
		], 
		string="Tipo", 
		required=True
	)
	evidencia = fields.Boolean(
		string="Para evidencia", 
		default=False, 
		help='Indica si el tipo de documento sera considerado como evidencia de viaje.'
	)
	dmc = fields.Boolean(
		string="Para DMC", 
		default=False, 
		help='Indica si este tipo de documento es considerado como Documento Maestro del Cliente'
	)
	detalles = fields.Text(
		string="Detalles", 
		default="", 
		help=""
	)
