# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class trafitec_ubi_responsable(models.Model):
	_name = 'trafitec.responsable'
	_description ='Responsable'

	responsable = fields.Many2one(
		'trafitec.ubicacion', 
		string='Responsable'
	)
	nombre_responsable = fields.Char(
		string="Nombre", 
		required=True
	)
	email_responsable = fields.Char(
		string="Correo Electronico", 
		required=True
	)
	telefono_responsable = fields.Char(
		string="Teléfono", 
		required=True
	)
