# -*- coding: utf-8 -*-

from odoo import models, fields

class TrafitecCotizacionesEvidencias(models.Model):
    _name = 'trafitec.cotizaciones.evidencias'
    _description='evidencias cotizaciones'

    image_filename = fields.Char('Nombre del archivo')
    evidencia_file = fields.Binary(
    	string='Archivo', 
    	required=True
    )
    cotizacion_id = fields.Many2one(
    	comodel_name='trafitec.cotizacion', 
    	string='Cotización', 
    	ondelete='cascade'
    )
    