# -*- coding: utf-8 -*-

from odoo import models, fields


class TrafitecEtiquetas(models.Model):
    _name = "trafitec.etiquetas"
    _description = "Etiquetas"
    
    name = fields.Char(
        string="Nombre",
        required=True
    )
    tipovalor = fields.Selection(
        [
            ("Numerico", "Numerico"),
            ("Texto", "Texto"),
            ("Booleano", "Booleano"),
            ("Entero", "Entero")
        ],
        string="Tipo de valor",
        required=True
    )
