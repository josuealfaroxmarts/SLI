# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class TrafitecSlitrackRegistro(models.Model):
    _name = "trafitec.slitrack.registro"
    _description = "SLI Track Registro"
    _order = "fechahorag desc"

    viaje_id = fields.Many2one(
        string="Viaje", 
        comodel_name="trafitec.viajes"
    )
    fechahorad = fields.Datetime(string="Fecha hora dispositivo")
    fechahorag = fields.Datetime(string="Fecha hora de generación")
    latitud = fields.Float(
        string="Latitud", 
        default=0, 
        digits=(10, 10)
    )
    longitud = fields.Float(
        string="Longitud", 
        default=0, 
        digits=(10, 10)
    )
    velocidad = fields.Float(
        string="Velocidad", 
        default=0, 
        digits=(10, 10)
    )
    detalles = fields.Char(
        string="Detalles", 
        default=""
    )
    proveedor = fields.Selection(
        string="Tipo", 
        selection=[
            ("slitrack", "SLI Track"),
            ("manual", "Manual")
        ],
        default="manual"
    )
    
    def unlink(self):
        for r in self:
            if r.proveedor in ("geotab", "slitrack"):
                raise UserError(_(
                    "Solo se pueden borrar los registros de tipo manual."
                ))
        return super(TrafitecSlitrackRegistro, self).unlink()

    @api.constrains
    def _validar(self):
        if not self.create_date:
            raise UserError(_("Debe especificar la fecha y hora."))

        if self.latitud == 0 and self.longitud == 0:
            raise UserError(_("Debe especificar la latitud y longitud."))

    def action_vermapa(self):
        return {
            "type": "ir.actions.act_url",
            "url": (
                "http://maps.google.com/maps?q=loc:"
                + str(self.latitud)
                + ","
                + str(self.longitud)
            ),
            "target": "blank",
        }