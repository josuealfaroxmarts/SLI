# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecBuques(models.Model):
	_name = 'trafitec.buques'
	_description ='buques'

	name = fields.Char(
		string='Nombre', 
		required=True
	)
	detalles = fields.Text(string='Detalles')
