# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecMunicipios(models.Model):
    _name = "trafitec.municipios"
    _description = "Municipios"

    name = fields.Char(string="Nombre completo")
    name_value = fields.Char(
        string="Nombre del municipio",
        required=True
    )
    estado = fields.Many2one(
        "res.country.state",
        string="Estado",
        ondelete="restrict",
        domain=[("country_id", "=", 157)],
        required=True
    )
    pais = fields.Many2one(
        "res.country",
        string="Pais",
        ondelete="restrict",
        default="_devuelve_mexico",
        required=True
    )

    @api.onchange("pais")
    def _onchange_pais(self):
        for rec in self:
            if self.pais:
                return {"domain": {
                    "estado": [("country_id", "=", rec.pais.id)]
                }}

    @api.model
    def _devuelve_mexico(self):
        return self.env["res.country"].search([("code", "=", "MX")])

    @api.model
    def create(self, vals):
        estado = self.env["res.country.state"].search([
            ("id", "=", vals["estado"])
        ])
        vals["name"] = str(vals["name_value"]) + ", " + str(estado.name)
        return super(TrafitecMunicipios, self).create(vals)

    def write(self, vals):
        if "name_value" in vals:
            nom = vals["name_value"]
        else:
            nom = self.name_value
        if "estado" in vals:
            estado = self.env["res.country.state"].search([
                ("id", "=", vals["estado"])
            ])
            vals["name"] = str(nom) + ", " + str(estado.name)
        else:
            vals["name"] = str(nom) + ", " + str(self.estado.name)
        return super(TrafitecMunicipios, self).write(vals)
