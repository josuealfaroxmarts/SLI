# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class trafitec_etiquetas(models.Model):
	_name = 'trafitec.etiquetas'
	_description ='etiquetas'
	name = fields.Char(
		string="Nombre", 
		required=True
	)
	tipovalor = fields.Selection(
		[
			('Numerico', 'Numerico'), 
			('Texto', 'Texto'), 
			('Booleano', 'Booleano'), 
			('Entero', 'Entero')
		],
		string="Tipo de valor", 
		required=True
	)