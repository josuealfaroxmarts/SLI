from odoo import api, fields, models, _


class TrafitecRemolques(models.Model):
	_name = "trafitec.remolques"
	_description = "remolques"
	
	name = fields.Char(
		string="No. económico",
		required=True,
		help="Número económico que identifica el "
		     "remolque/dolly de manera única."
	)
	placas = fields.Char(
		string="Placas",
		required=True,
		help="Número de placas."
	)
	ejes = fields.Integer(
		string="Número de ejes",
		required=True,
		default=1,
		help="Número de ejes del remolque."
	)
	tipo = fields.Selection(
		string="Tipo",
		selection=[
			("ninguno", "Ninguno"),
			("remolque", "Remolque"),
			("dolly", "Dolly")
		],
		default="ninguno",
		required=True
	)
	descripcion = fields.Char(
		string="Descripción",
		help="Detalles sobre el remolque/dolly."
	)
	active = fields.Boolean(
		string="Activo",
		default=True,
		help="Estado del remolque/dolly, activo o inactivo."
	)

