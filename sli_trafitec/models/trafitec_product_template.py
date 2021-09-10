# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecProductTemplate(models.Model):
	_inherit = "trafitec.product.template"
	_description = "Product Template"

	trafi_product_id = fields.One2many(
		"trafitec.product.etiqueta", 
		"product_id"
	)
	es_flete = fields.Boolean(
		string="Es flete", 
		default=False, 
		help="Indica si este producto sera considerado como flete para procesos del sistema."
	)
	