# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecLocalidad(models.Model):
    _name = "trafitec.localidad"
    _description = "Localidad"

    name = fields.Char(string="Nombre")
    name_value = fields.Char(
        string="Nombre de la Localidad",
        required=True
    )
    codigopostal = fields.Char(string="Codigo postal")
    municipio = fields.Many2one(
        "trafitec.municipios",
        string="Municipio",
        required=True
    )
    comentarios = fields.Text(string="Comentarios")

    @api.model
    def create(self, vals):
        municipio_id = vals["municipio"]
        municipio_obj = self.env["trafitec.municipios"].search([
            ("id", "=", municipio_id)
        ])
        vals["name"] = str(vals["name_value"]) + ", " + str(municipio_obj.name)

        return super(TrafitecLocalidad, self).create(vals)

    def write(self, vals):
        if "name_value" in vals:
            nom = vals["name_value"]
        else:
            nom = self.name_value
        if "municipio" in vals:
            municipio_obj = self.env["trafitec.municipios"].search([
                ("id", "=", vals["municipio"])
            ])
            vals["name"] = nom + ", " + str(municipio_obj.name)
        else:
            vals["name"] = nom + ", " + self.municipio.name
        return super(TrafitecLocalidad, self).write(vals)
