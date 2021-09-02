# -*- coding: utf-8 -*-
from typing_extensions import Required
from odoo import models, fields, api, _


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    bill_count = fields.Integer(
        string="Bill count",
        Required=False,
        readonly=False
    )