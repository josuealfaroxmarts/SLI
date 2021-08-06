

class TrafitecAbonos(models.Model):
	_name = "trafitec.abonos"
	_description = "Abonos"

	cargo_id = fields.Integer(string="Id del padre")
	monto = fields.Float(string="monto")
	detalle = fields.Text(string="detalle")
	cobradoen = fields.Char(string="Cobrado en")
	descuento_abono_id = fields.Many2one("trafitec.descuentos.abono",string="Id del abono a descuento")
	comision_abono_id = fields.Many2one("trafitec.comisiones.abono", string="Id del abono a comision")