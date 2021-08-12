from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class TrafitecDescuentos(models.Model):
	_name = "trafitec.descuentos"
	_description = "Descuentos"
	_order = "id desc"
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_rec_name = "id"

	name = fields.Char(string="Folio")
	viaje_id = fields.Many2one(
		"trafitec.viajes",
		string="Viaje",
		tracking=True
	)
	flete_asociado = fields.Float(
		string="Flete asociado",
		related="viaje_id.flete_asociado",
		readonly=True
	)
	asociado_id = fields.Many2one(
		"res.partner",
		string="Asociado",
		domain="[('asociado','=',True)]", required=True)
	operador_id = fields.Many2one(
		"res.partner",
		string="Operador",
		domain="[('operador','=',True)]"
	)
	concepto = fields.Many2one(
		"trafitec.concepto.anticipo",
		string="Concepto",
		required=True
	)
	monto = fields.Float(
		string="Monto",
		required=True,
		tracking=True
	)
	proveedor = fields.Many2one(
		"res.partner",
		string="Proveedor",
		domain="[('supplier_rank','=',True)]", tracking=True)
	cobro_fijo = fields.Boolean(
		string="Cobro fijo",
		tracking=True
	)
	monto_cobro = fields.Float(
		string="Cantidad",
		tracking=True
	)
	folio_nota = fields.Char(
		string="Folio nota",
		tracking=True
	)
	comentarios = fields.Text(
		string="Comentarios", 
		tracking=True
	)
	company_id = fields.Many2one(
		"res.company", 
		"Company",
		default=lambda self: self.env["res.company"]._company_default_get("trafitec.descuentos"), 
		tracking=True
	)
	abono_id = fields.One2many(
		"trafitec.descuentos.abono",
		"abonos_id", 
		tracking=True
	)
	fecha = fields.Date(
		string="Fecha", 
		readonly=True, 
		index=True, 
		copy=False,
		default=fields.Datetime.now, 
		tracking=True
	)
	state = fields.Selection(
		string="Estado", 
		selection=[
			("borrador", "Borrador"), 
			("activo", "Aprobado"), 
			("cancelado", "Cancelado")
		], 
		default="borrador", 
		tracking=True
	)
	es_combustible = fields.Boolean(
		string="Vale de combustible", 
		default=False, 
		tracking=True
	)
	es_combustible_litros = fields.Float(
		string="Litros", 
		default=0, 
		tracking=True
	)
	es_combustible_costoxlt = fields.Float(
		string="Costo por litro", 
		default=0, 
		tracking=True
	)
	es_combustible_total = fields.Float(
		string="Total", 
		default=0, 
		compute="compute_es_combustible_total", 
		store=True, 
		tracking=True,
		help="Total sin comisión."
	)
	es_combustible_pcomision = fields.Float(
		string="Porcentaje comisión (%)",
		default=0, 
		tracking=True
	)
	es_combustible_comision = fields.Float(
		string="Comisión", 
		default=0,
		compute="compute_es_combustible_comision",
		store=True,
		tracking=True
	)
	es_combustible_totalcomision = fields.Float(
		string="Total comision", 
		default=0,
		compute="compute_es_combustible_totalcomision",
		store=True,
		tracking=True,
		help="Total con comisión."
	)

	@api.depends("es_combustible_litros", "es_combustible_costoxlt")
	def compute_es_combustible_total(self):
		self.es_combustible_total = self.es_combustible_litros*self.es_combustible_costoxlt

	@api.depends("es_combustible_total", "es_combustible_pcomision")
	def compute_es_combustible_comision(self):
		self.es_combustible_comision = self.es_combustible_total*(self.es_combustible_pcomision/100)

	@api.depends("es_combustible_total", "es_combustible_comision")
	def compute_es_combustible_totalcomision(self):
		self.es_combustible_totalcomision = self.es_combustible_total+self.es_combustible_comision

	def action_aprobar(self):
		self.ensure_one()
		error = False
		errores = ""

		if self.monto <= 0:
			error = True
			errores += "Debe especificar el monto.\n"

		if not self.proveedor:
			error = True
			errores += "Debe especificar el proveedor.\n"

		if not self.folio_nota:
			error = True
			errores += "Debe especificar el folio de la nota.\n"

		if error:
			raise UserError(errores)

		self.state = "activo"


	def action_borrador(self):
		self.ensure_one()
		self.state = "borrador"


	@api.constrains("monto", "abono_total")
	def _check_monto_abono(self):
		if self.monto and self.abono_total:
			if self.abono_total > self.monto:
				raise UserError(("Aviso !\nEl abono del descuento ({}) debe ser manor o igual al saldo del descuento ({}).".format(self.abono_total, self.monto)))


	def copy(self):
		raise UserError("No se permite duplicar descuentos.")


	def unlink(self):
		raise UserError("No se permite borrar descuentos.")

		if self.abono_total > 0:
			raise UserError(_("Aviso !\nNo se puede eliminar un descuento que tenga abonos."))
		return super(trafitec_descuentos, self).unlink()


	@api.depends("abono_id.name")
	def _compute_abono_total(self):
		self.abono_total = sum(line.name for line in self.abono_id)

	abono_total = fields.Float(string="Abonos", compute="_compute_abono_total",store=True)


	@api.depends("abono_total", "monto")
	def _compute_saldo(self):
		if self.abono_total:
			self.saldo = self.monto - self.abono_total
		else:
			self.saldo = self.monto

	saldo = fields.Float(string="Saldo", compute="_compute_saldo",store=True)

	@api.constrains("monto")
	def _check_monto(self):
		if self.monto <= 0:
			raise UserError((
				"Aviso !\nEl monto debe ser mayor a cero."))

	@api.constrains("monto_cobro")
	def _check_monto_cobro(self):
		if self.cobro_fijo == True:
			if self.monto_cobro <= 0:
				raise UserError((
					"Aviso !\nEl monto del cobro debe ser mayor a cero."))


	@api.onchange("viaje_id")
	def _onchange_viaje(self):
		if self.viaje_id:
			self.asociado_id = self.viaje_id.asociado_id
			self.operador_id = self.viaje_id.operador_id

	@api.model
	def create(self, vals):
		if "company_id" in vals:
			vals["name"] = self.env["ir.sequence"].with_context(force_company=vals["company_id"]).next_by_code(
				"Trafitec.Descuentos") or ("Nuevo")
		else:
			vals["name"] = self.env["ir.sequence"].next_by_code("Trafitec.Descuentos") or ("Nuevo")

		v_id = super(TrafitecDescuentos, self).create(vals)

		if "viaje_id" in vals:
			valores = {"viaje_id": vals["viaje_id"], "monto": vals["monto"], "tipo_cargo": "descuentos","asociado_id" : vals["asociado_id"], "descuento_id" : v_id.id}
		else:
			valores = {"monto": vals["monto"], "tipo_cargo": "descuentos",
			           "asociado_id": vals["asociado_id"], "descuento_id" : v_id.id}
		self.env["trafitec.cargos"].create(valores)
		return v_id


	def write(self, vals):
		if "viaje_id" in vals:
			viaje_id = vals["viaje_id"]
		else:
			if self.viaje_id:
				viaje_id = self.viaje_id.id
			else:
				viaje_id = None

		if "monto" in vals:
			monto = vals["monto"]
		else:
			monto = self.monto
		if "asociado_id" in vals:
			asociado_id = vals["asociado_id"]
		else:
			asociado_id = self.asociado_id.id

		valores = {"viaje_id": viaje_id, "monto": monto, "tipo_cargo": "descuentos",
		           "asociado_id": asociado_id, "descuento_id": self.id}

		obc_cargos = self.env["trafitec.cargos"].search(
			["&", ("descuento_id", "=", self.id), ("tipo_cargo", "=", "descuentos")])
		if len(obc_cargos) == 0:
			self.env["trafitec.cargos"].create(valores)
		else:
			obc_cargos.write(valores)

		return super(TrafitecDescuentos, self).write(vals)


	"""
	Cancela descuento verificando si tiene abonos.
	"""

	def action_cancelar(self):
		for rec in self:
			abonos_obj = self.env["trafitec.descuentos.abono"]
			abonos_dat = abonos_obj.search([("abonos_id", "=", rec.id)])
			if abonos_dat and len(abonos_dat) > 0:
				raise UserError(("Este descuento tiene abonos."))

			if rec.viaje_id:
				if rec.viaje_id.descuento_combustible_id.id == rec.id:
					rec.viaje_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).write({"descuento_combustible_id": False})
	
			rec.state = "cancelado"

