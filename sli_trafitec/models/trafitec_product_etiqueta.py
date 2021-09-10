# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecProductEtiqueta(models.Model):
	_name = "trafitec.product.etiqueta"
	_description ="Etiqueta Producto"

	product_id = fields.Many2one(
		"trafitec.product.template", 
		string="Product"
	)
	etiqueta_id = fields.Many2one(
		"trafitec.tipo.presentacion", 
		string="Presentación"
	)
