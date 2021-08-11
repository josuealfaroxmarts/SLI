# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecTipocargosadicionales(models.Model):
	_name = 'trafitec.tipocargosadicionales'
	_description ='tipo cargos adicionales'

	name = fields.Char(
		string="Nombre", 
		required=True
	)
	product_id = fields.Many2one(
		'product.product', 
		string='Producto', 
		required=True
	)
	validar_en_cr = fields.Boolean(
		string="Validar en CR", 
		help='Validar este concepto en el contra recibo y carta porte (Obtiene los cargos adicionales del cada viaje del contrarecibo y verifica su existencia en los conceptos de la carta porte.).'
	)
