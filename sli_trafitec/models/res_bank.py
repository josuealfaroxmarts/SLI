# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class ResBank(models.Model):
    _inherit = "res.bank"

    no_institucion = fields.Char(
    	string="No. de institución", 
    	required=True
    )
    clave_institucion = fields.Char(
        string="Clave de la institución",
        required=True
    )
    exportar = fields.Boolean(string="Exportar")
