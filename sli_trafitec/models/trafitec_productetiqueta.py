# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecProductetiqueta(models.Model):
	_name = 'trafitec.product'
	_description ='Etiqueta producto'

	product_id = fields.Many2one(
		'product.template', 
		string='Product'
	)
	etiqueta_id = fields.Many2one(
		'trafitec.tipopresentacion', 
		string='Presentación'
	)
