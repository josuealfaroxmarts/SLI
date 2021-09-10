# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecStatusCliente(models.Model) :
	_name = "trafitec.status.cliente"
	_description ="Status Cliente"

	status = fields.Char(
		string="Estatus", 
		required=True
	)
