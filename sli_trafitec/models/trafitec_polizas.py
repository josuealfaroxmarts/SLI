# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class TrafitecPolizas(models.Model):
	_name = "trafitec.polizas"
	_description ="Polizas"
	_order = "id desc"

	name = fields.Char(
		string="Folio",
		required=True
	)
	aseguradora_id = fields.Many2one(
		"res.partner",
		string="Aseguradora",
		required=True,
		domain="[('aseguradora','=','True')]"
	)
	porcentaje_aseg = fields.Float(
		string="Porcentaje aseguradora",
		required=True
	)
	porcentaje_clie = fields.Float(
		string="Porcentaje cliente",
		required=True
	)
	vigencia_desde = fields.Date(
		string="Vigencia desde",
		required=True
	)
	vigencia_hasta = fields.Date(
		string="Vigencia hasta",
		required=True
	)
	estado_poliza = fields.Selection(
		[
			("vigente", "Vigente"),
			("cancelada", "Cancelada")
		], string="Estado de la póliza",
		required=True
	)
	activo = fields.Boolean(string="Activo")
	detalles = fields.Text(string="Detalles")