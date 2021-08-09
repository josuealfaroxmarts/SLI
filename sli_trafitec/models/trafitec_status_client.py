# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class trafitec_status_client(models.Model) :
	name = 'trafitec.status'
	status = fields.Char(
		string="Estatus", 
		required=True
	)
	_description ='status'
