# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class TrafitecAsignaciones(models.Model):
    _name = "trafitec.asignaciones"
    _description = "Asignaciones"

    asignadoa_id = fields.Many2one(
        string="Usuario",
        comodel_name="res.users",
        help="Usuario al que se le asigno el viaje."
    )
    viaje_id = fields.Many2one(
        string="Viaje",
        comodel_name="trafitec.viajes",
        help="Viaje asignado."
    )
    tipo = fields.Selection(
        string="Tipo",
        selection=[("alcrear", "Al crear"), ("almodificar", "Al modificar")],
        default="alcrear"
    )
