# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class TrafitecViajesEvidencias(models.Model):
    _name = "trafitec.viajes.evidencias"
    _description = "Viajes Evidencias"
    
    name = fields.Selection(
        [
            ("evidencia_de_viaje", "Evidencia De Viaje"),
            ("carta_porte", "Carta Porte"),
            ("carta_porte_xml", "Carta Porte XML")
        ],
        string="Tipo",
        required=True,
        default="evidencia_de_viaje"
    )
    image_filename = fields.Char("Nombre del archivo")
    evidencia_file = fields.Binary(
        string="Archivo", 
        required=True
    )
    linea_id = fields.Many2one(
        "trafitec.viajes",
        string="Evidencia id",
        ondelete="cascade"
    )