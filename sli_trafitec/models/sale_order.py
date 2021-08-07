

class trafitec_saleorder(models.Model):
	_inherit = 'sale.order'
	trafitec_cotizacion_id = fields.Many2one(string='Cotización trafitec', comodel_name='trafitec.cotizacion')
	trafitec_cotizacion_txt = fields.Char(string='Cotizacion trafitec', related='trafitec_cotizacion_id.name', readonly=True, store=True)

	def action_cancel(self):
		contexto = self._context
		print("--CONTEXTO AL CANCELAR SALE.ORDER--")
		print(contexto)
		trafitec_cancelar = contexto.get("trafitec_cancelar", False)
		if not trafitec_cancelar:
			if self.trafitec_cotizacion_id:
				raise UserError(_("Este pedido de ventas esta relacionado con una cotización de trafitec."))

		return super(trafitec_saleorder, self).action_cancel()

	@api.model
	def create(self, vals):
		return super(trafitec_saleorder, self).create(vals)