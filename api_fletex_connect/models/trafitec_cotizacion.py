# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TrafitecCotizacion(models.Model):
    _inherit = "trafitec.cotizacion"

    id_fletex = fields.Integer()
    send_to_api = fields.Boolean()

    def action_available(self):
        if self.state == "Enviada":
            self.send_to_api = True
        super(TrafitecCotizacion, self).action_available()
