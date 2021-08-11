# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
import xlsxwriter
import base64


class TrafitecTipopresentacion(models.Model):
	_name = 'trafitec.tipopresentacion'
	_description ='tipo presentacion'

	name = fields.Char(
		string="Nombre", 
		required=True
	)
