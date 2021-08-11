# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class ViajesXContrarecibo(models.Model):
	_name="trafitec.viajesxcontrarecibo"
	_description ="Viajesx contrarecibo"
	viaje_id=fields.Many2one(string="Viaje", comodel_name="trafitec.viajes")
	contrarecibo_id=fields.Many2one(string="Contra recibo", comodel_name="trafitec.contrarecibo")
	factura_id=fields.Many2one(string="Factura", comodel_name="account.move")

	@api.model
	def create(self, vals):
		viaje = self.env["trafitec.viajes"].search([("id", "=", vals["viaje_id"])])
		viaje.write({"en_contrarecibo": True, "factura_proveedor_id": vals["factura_id"]})
		return super(viajesxcontrarecibo, self).create(vals)


	def unlink(self):
		for reg in self:
			viaje=self.env["trafitec.viajes"].search([("id", "=", reg.viaje_id.id)])
			viaje.write({"en_contrarecibo":False, "factura_proveedor_id":False})
		return super(viajesxcontrarecibo, self).unlink()
