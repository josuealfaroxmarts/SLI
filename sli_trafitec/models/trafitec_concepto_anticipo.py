# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecConceptoAnticipo(models.Model):
    _name = "trafitec.concepto.anticipo"
    _description = "Trafitec Concepto De Anticipo"

    name = fields.Char(
    	string="Concepto", 
    	required=True
    )
    requiere_orden = fields.Boolean(string="Requiere orden de carga")
