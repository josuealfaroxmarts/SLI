# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from xml.dom import minidom


class trafitec_facturas_cancelar(models.TransientModel):
	_name = "trafitec.facturas.cancelar"
	_description ="Facturas cancelar"

	factura_id = fields.Many2one(string="Factura", comodel_name="account.move", help="Factura que se cancelara.")
	detalles = fields.Char(string="Detalles", default="", help="Detalles.")

	def cancelar(self):
		for rec in self:
			for v in rec.factura_id.viajes_id:
				vobj = rec.env["trafitec.viajes"].search([("id", "=", v.id)])
				vobj.write({"factura_cliente_id": False, "en_factura": False})
			
			rec.factura_id.write({"cancelacion_detalles": self.detalles})
			factura = rec.factura_id.action_cancel()