# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
import xlsxwriter
import base64


class TrafitecTipoPresentacion(models.Model):
	_name = "trafitec.tipo.presentacion"
	_description ="Tipo De Presentacion"

	name = fields.Char(
		string="Nombre", 
		required=True
	)
