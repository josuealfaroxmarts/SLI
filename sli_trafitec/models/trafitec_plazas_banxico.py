# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecPlazasBanxico(models.Model):
    _name = "trafitec.plazas.banxico"
    _description = "Plazas Banxico"

    name = fields.Char(
        string="Nombre",
        required=True
    )
    numero_plaza = fields.Char(
        string="Número de plaza",
        required=True
    )
    display_name = fields.Char(
        string="Nombres",
        compute="_compute_display_name"
    )

    def _compute_display_name(self):
        self.display_name = "{} - {}".format(self.name, self.numero_plaza)
