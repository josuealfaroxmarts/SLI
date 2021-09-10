# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecTipoCargosAdicionales(models.Model):
	_name = "trafitec.tipo.cargos.adicionales"
	_description ="Tipo De Cargos Adicionales"

	name = fields.Char(
		string="Nombre", 
		required=True
	)
	product_id = fields.Many2one(
		"product.product", 
		string="Producto", 
		required=True
	)
	validar_en_cr = fields.Boolean(
		string="Validar en CR", 
		help="Validar este concepto en el contrarecibo y " + 
		"carta porte (Obtiene los cargos adicionales de " + 
		"cada viaje del contrarecibo y verifica su existencia " + 
		"en los conceptos de la carta porte)."
	)
