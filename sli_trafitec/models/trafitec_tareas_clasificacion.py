
from odoo import api, fields, models


class TrafitecTareasClasificacion(models.Model):
	_name = "trafitec.tareas.clsificacion"
	_description="Clasificaciones tareas"

	name = fields.Char(string="Nombre", required=True)
	asignara_id = fields.Many2one(string="Asignar a",comodel_name="res.users",help="Usuario al que se asignaran automaticamente las tareas al clasificarla.")
	tipo = fields.Selection(string="Tipo", selection=[("principal","Principal"), ("secundaria","Secundaria")], required = True, help="")
	clasificacion_id = fields.Many2one(string="Clasificación",comodel_name="trafitec.tareas.clsificacion")
	state = fields.Selection(string="Estado", selection=[("activo", "Activo"), ("inactivo", "Inactivo")], default="activo")
