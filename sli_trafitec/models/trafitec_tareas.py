# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api, tools


class TrafitecTareas(models.Model):
	_name = "trafitec.tareas"
	_description="Tareas"
	_order = "id desc"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	
	name = fields.Char(
		string="Nombre",
		required=True,
		tracking=True
	)
	detalles = fields.Text(
		string="Detalles",
		required=True,
		tracking=True
	)
	asignado_usuario_id = fields.Many2one(
		string="Asignado a",
		comodel_name="res.users",
		tracking=True
	)
	revision_usuario_id = fields.Many2one(
		string="Usuario que reviso",
		comodel_name="res.users",
		tracking=True
	)
	revision_fechahora = fields.Datetime(string="Fecha y hora de revisión")
	validado_usuario_id = fields.Many2one(
		string="Usuario que valido",
		comodel_name="res.users",
		tracking=True
	)
	validado_fechahora = fields.Datetime(string="Fecha y hora de validación")
	cerrado_usuario_id = fields.Many2one(
		string="Usuario que cerro",
		comodel_name="res.users",
		tracking=True
	)
	cerrado_fechahora = fields.Datetime(string="Fecha y hora de cierre")
	clasificacion_principal_id = fields.Many2one(
		string="Clasificación principal",
		comodel_name="trafitec.tareas.clasificacion",
		tracking=True,
		domain=[
			('tipo','=','principal'), ('state','=','activo')
		]
	)
	clasificacion_secundaria_id = fields.Many2one(
		string="Clasificación secuendaria",
		comodel_name="trafitec.tareas.clasificacion",
		tracking=True,
		required=True,
		domain=[
			('tipo','=','secundaria'), ('state','=','activo')
		]
	)
	state = fields.Selection(
		string="Estado",
		selection=[
			("nuevo", "Nuevo"),
			("revisado", "Revisado"),
			("validado", "Validado"),
			("cerrado", "Cerrado"),
			("cancelado", "Cancelado")
		],
		default="nuevo",
		tracking=True
	)

	def action_revisar(self):
		self.revision_usuario_id = self.env.user.id
		self.revision_fechahora = datetime.datetime.now()
		self.state = "revisado"

	def action_validar(self):
		self.validado_usuario_id = self.env.user.id
		self.validado_fechahora = datetime.datetime.now()
		self.state = "validado"

	def action_cerrar(self):
		self.cerrado_usuario_id = self.env.user.id
		self.cerrado_fechahora = datetime.datetime.now()
		self.state = "cerrado"

	def action_cancelar(self):
		self.state = "cancelado"
		
	@api.model
	def create(self, vals):
		try:
			clas_obj = self.env["trafitec.tareas.clasificacion"]
			clas_dat = clas_obj.search([("id", "=", vals["clasificacion_secundaria_id"])])

			if not vals["asignado_usuario_id"] and len(clas_dat) == 1:
				vals["asignado_usuario_id"] = clas_dat.asignara_id.id
			
			if not vals["clasificacion_principal_id"] and len(clas_dat) == 1 and clas_dat.clasificacion_id:
				vals["clasificacion_principal_id"] = clas_dat.clasificacion_id.id
		except:
			print("**Error al asignar el usuario a tarea.")
		
		return super(TrafitecTareas, self).create(vals)
