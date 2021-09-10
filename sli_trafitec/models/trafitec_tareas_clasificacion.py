# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TrafitecTareasClasificacion(models.Model):
	_name = "trafitec.tareas.clasificacion"
	_description = "Clasificaciones Tareas"

	name = fields.Char(
		string="Nombre",
		required=True
	)
	asignara_id = fields.Many2one(
		string="Asignar a",
		comodel_name="res.users",
		help="Usuario al que se asignaran automaticamente" +
		     " las tareas al clasificarla."
	)
	tipo = fields.Selection(
		string="Tipo",
		selection=[
			("principal", "Principal"), 
			("secundaria", "Secundaria")
		],
		required=True
	)
	clasificacion_id = fields.Many2one(
		string="Clasificación",
		comodel_name="trafitec.tareas.clasificacion"
	)
	state = fields.Selection(
		string="Estado",
		selection=[
			("activo", "Activo"), 
			("inactivo", "Inactivo")
		],
		default="activo"
	)
