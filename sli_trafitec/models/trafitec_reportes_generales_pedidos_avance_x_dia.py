# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecReportesGeneralesPedidosAvanceXDia(models.Model):
	_name = "trafitec.reportes.generales.pedidos.avance.x.dia"
	_description = "Reportes Generales Pedidos Avance X Dia"
	
	buscar_id = fields.Many2one(
		string="Buscar",
		comodel_name="trafitec.reportes.generales.pedidos.avance.buscar"
	)
	cotizacion = fields.Char(
		string="Cotizacion", 
		default=""
	)
	cliente = fields.Char(
		string="Cliente", 
		default=""
	)
	ano = fields.Integer(
		string="Año", 
		default=0
	)
	mes = fields.Integer(
		string="Mes", 
		default=0
	)
	dia = fields.Integer(
		string="Dia", 
		default=0
	)
	viajes = fields.Integer(
		string="Viajes", 
		default=0
	)
	peso = fields.Float(
		string="Peso", 
		default=0
	)
