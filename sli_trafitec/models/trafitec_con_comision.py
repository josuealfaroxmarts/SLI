
class TrafitecConComision(models.Model):
	_name = "trafitec.con.comision"
	_description ="Comision"

	name = fields.Char(string="Folio del viaje", readonly=True)
	fecha = fields.Date(string="Fecha", readonly=True)
	comision = fields.Float(string="Comision", readonly=True)
	abonos = fields.Float(string="Abonos", readonly=True)
	saldo = fields.Float(string="Saldo", readonly=True)
	asociado_id = fields.Many2one("res.partner", string="Asociado", domain="[("asociado","=",True)]", readonly=True)
	tipo_viaje = fields.Char(string="Tipo de viaje", readonly=True)
	cargo_id = fields.Many2one("trafitec.cargos",string="ID comision")
	line_id = fields.Many2one(comodel_name="trafitec.contrarecibo", string="Contrarecibo id", ondelete="cascade")
	viaje_id = fields.Many2one("trafitec.viajes", string="Viaje ID")
	cobrado = fields.Boolean(string="Cobrado", default=False)
