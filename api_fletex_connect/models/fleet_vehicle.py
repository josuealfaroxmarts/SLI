# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    id_fletex_truck = fields.Integer()
    id_fletex_trailer = fields.Integer()
    send_to_api = fields.Boolean(default=False)
    status_vehicle = fields.Selection(
        [("approved", "Aprobado"),
         ("rejected", "Rechazado"),
         ("onhold", "En Espera")],
        string="Status",
        default="onhold"
    )
    poliza_approved = fields.Boolean(
        string="Poliza aprobada",
        default=False
    )
    circulacion_approved = fields.Boolean(
        string="Tarjeta de circulacion aprobada",
        default=False
    )
    bill_count = fields.Integer(string="Bills Count")

    @api.onchange("status_vehicle")
    def _change_send_to_api(self):
        for fleet in self:
            fleet.send_to_api = True