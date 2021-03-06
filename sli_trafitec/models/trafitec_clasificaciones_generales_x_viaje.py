# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecClasificacionesGeneralesXViaje(models.Model):
    _name = "trafitec.clasificaciones.generales.x.viaje"
    _description = "Clasificaciones Generales X Viaje"

    viaje_id = fields.Many2one(
        string="Viaje",
        comodel_name="trafitec.viajes"
    )
    clasificacion_id = fields.Many2one(
        string="Calificación",
        comodel_name="trafitec.clasificaciones.generales",
        required=True
    )
    operador_nombre = fields.Char(
        string="Operador",
        related="viaje_id.operador_id.display_name",
        store=True
    )
    asociado_nombre = fields.Char(
        string="Asociado",
        related="viaje_id.asociado_id.display_name",
        store=True
    )
    considerar = fields.Selection(
        string="Considerado como",
        related="clasificacion_id.considerar",
        store=True
    )
    _sql_constraints = [
        (
            "viaje_clasificacion_uniq",
            "unique(viaje_id, clasificacion_id)",
            "La calificación debe ser unica en el viaje."
        )
    ]
