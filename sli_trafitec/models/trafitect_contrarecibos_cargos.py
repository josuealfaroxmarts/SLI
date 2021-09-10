# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecContrarecibosCargos(models.Model):
	_name = "trafitec.contrarecibos.cargos"
	_description ="Contrarecibos Cargos"
	
	tipo_cargo_id = fields.Many2one(
		string="Tipo de cargo adicional",
		comodel_name="trafitec.tipo.cargos.adicionales",
		required=True
	)
	valor = fields.Float(
		string="Valor",
		default=0,
		required=True
	)
	contrarecibo_id = fields.Many2one(
		string="Contrarecibo",
		comodel_name="trafitec.contrarecibo"
	)
	viaje_id = fields.Many2one(
		string="Viaje",
		comodel_name="trafitec.viajes"
	)
