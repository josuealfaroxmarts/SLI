## -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class TrafitecCargosxAbonos(models.Model):
	_name="trafitec.cargosx.abonos"
	_description ="Abonos Cargos X"

	cargosx_id = fields.Many2one(
		comodel_name="trafitec.cargosx",
		string="Cargo",required=True)
	abono = fields.Float(string="Abono",default=0,required=True)
	generadoen = fields.Selection(string="Generado en",selection=[("sistema","Sistema"),("manual","Manual"),("contrarecibo","Contra recibo"),("factura","Factura")],default="sistema")
	observaciones = fields.Text(string="Observaciones",default="",required=True,help="Observaciones del abono.")

