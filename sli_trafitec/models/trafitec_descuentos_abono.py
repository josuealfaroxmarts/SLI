


class trafitec_descuentos_abono(models.Model):
	_name = "trafitec.descuentos.abono"
	_description = "Descuentos y abonos"

	name = fields.Float(string="Abono", required=True)
	fecha = fields.Date(string="Fecha", required=True, default=fields.Datetime.now)
	observaciones = fields.Text(string="Observaciones")
	tipo = fields.Selection([("manual","Manual"),("contrarecibo","Contra recibo")],string="Tipo", default="manual")
	abonos_id = fields.Many2one("trafitec.descuentos", ondelete="cascade")
	contrarecibo_id = fields.Many2one("trafitec.contrarecibo", ondelete="restrict")
	permitir_borrar = fields.Boolean(string="Permitir borrar", default=False)


	def unlink(self):
		#if self.tipo == "contrarecibo":
		#    if self.permitir_borrar != False:
		#        raise UserError(_(
		#            "Aviso !\nNo se puede eleminar un abono de un contra recibo."))
		#if self.tipo == "manual":
		#obj = self.env["trafitec.con.descuentos"].search([("descuento_fk", "=", self.abonos_id.id), ("linea_id.state", "=", "Nueva")])
		#for des in obj:
		#    res = des.saldo + self.name
		#    abonado = des.anticipo - res
		#    des.write({"saldo": res, "abonos": abonado, "abono": res})
		return super(trafitec_descuentos_abono, self).unlink()

	@api.constrains("name")
	def _check_abono(self):
		if self.name <= 0:
			raise UserError(_("Aviso !\nEl monto del abono debe ser mayor a cero."))

	@api.constrains("name")
	def _check_monto_mayor(self):
		obj_abono = self.env["trafitec.descuentos.abono"].search([("abonos_id","=",self.abonos_id.id)])
		amount = 0
		for abono in obj_abono:
			amount += abono.name

		#if amount > self.abonos_id.monto:
		#   raise UserError(_("Aviso !\nEl monto de abonos ha sido superado al monto del descuento."))


	@api.model
	def create(self, vals):
		id =  super(trafitec_descuentos_abono, self).create(vals)
		if "tipo" in vals:
			tipo = vals["tipo"]
		else:
			tipo = "manual"
		valores = {
			"descuento_abono_id" : id.id,
			"monto": vals["name"],
			"detalle": vals["observaciones"],
			"cobradoen" : "Descuento {}".format(tipo)
		}
		self.env["trafitec.abonos"].create(valores)
		if tipo == "manual":
			obj = self.env["trafitec.con.descuentos"].search([("descuento_fk","=",vals["abonos_id"]),("linea_id.state","=","Nueva")])
			for des in obj:
				res = des.saldo - vals["name"]
				abonado = des.anticipo - res
				des.write({"saldo":res, "abonos": abonado, "abono":res})
		return id


	def write(self, vals):
		if "name" in vals:
			monto = vals["name"]
		else:
			monto = self.name
		if "observaciones" in vals:
			detalle = vals["observaciones"]
		else:
			detalle = self.observaciones
		valores = {
			"monto": monto,
			"detalle": detalle
		}
		obj = self.env["trafitec.abonos"].search([("descuento_abono_id","=",self.id)])
		obj.write(valores)
		if self.tipo == "manual" and "name" in vals:
			obj = self.env["trafitec.con.descuentos"].search([("descuento_fk","=",self.abonos_id.id),("linea_id.state","=","Nueva")])
			for des in obj:
				if self.name > vals["name"]:
					res = des.saldo + (self.name - vals["name"])
				else:
					res = des.saldo - (vals["name"] - self.name)
				if res == 0:
					des.unlink()
				else:
					abonado = des.anticipo - res
					des.write({"saldo":res, "abonos": abonado, "abono":res})

		return super(trafitec_descuentos_abono, self).write(vals)