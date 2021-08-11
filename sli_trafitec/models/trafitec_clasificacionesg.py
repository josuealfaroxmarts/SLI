# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class trafitec_clasificacionesg(models.Model):
    _name = 'trafitec.clasificacionesg'
    _description = 'clasicaciones sg'

    name = fields.Char(
        string='Nombre',
        default='',
        required=True
    )
    aplica_viajes = fields.Boolean(
        string='Aplica a calificar viaje',
        default=False
    )
    aplica_crm_trafico_rechazo = fields.Boolean(
        string='Aplica a CRM Tráfico en rechazo',
        default=False
    )
    aplica_clasificacion_bloqueo_cliente = fields.Boolean(
        string='Aplica clasificación de bloqueo de cliente',
        default=False
    )
    considerar = fields.Selection([
            ('noespecificado', 'No especificado'),
            ('malo', 'Malo'),
            ('bueno', 'Bueno')
        ],
        string="Considerar",
        default='malo',
        required=True
    )
    state = fields.Selection([
            ('inactivo', 'Inactivo'),
            ('activo', 'Activo')
        ],
        string='Estado',
        required=True,
        default='activo'
    )
