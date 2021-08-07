
class TrafitecContrarecibosCargos(models.Model):
	_name = "trafitec.contrarecibos.cargos"
	_description ="Contrarecibos cargos"
	tipo_cargo_id = fields.Many2one(
		string="Tipo de cargo adicional",
		comodel_name="trafitec.tipocargosadicionales",
		required=True
	)
	valor = fields.Float(
		string="Valor",
		default=0,
		required=True
	)
	contrarecibo_id = fields.Many2one(
		string="Contra recibo",
		comodel_name="trafitec.contrarecibo"
	)

	viaje_id = fields.Many2one(
		string="Viaje",
		comodel_name="trafitec.viajes"
	)
