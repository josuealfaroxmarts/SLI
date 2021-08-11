# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class trafitec_viajes_evidencias(models.Model):
    _name = 'trafitec.viajes.evidencias'
    _description = 'viajes evidencias'
    
    name = fields.Selection([
            ('Evidencia de viaje', 'Evidencia de viaje'),
            ('Carta porte', 'Carta porte'),
            ('Carta porte xml', 'Carta porte xml')
        ],
        string="Tipo",
        required=True,
        default='Evidencia de viaje'
    )
    image_filename = fields.Char("Nombre del archivo")
    evidencia_file = fields.Binary(string="Archivo", required=True)
    linea_id = fields.Many2one(
        "trafitec.viajes",
        string="Evidencia id",
        ondelete='cascade'
    )