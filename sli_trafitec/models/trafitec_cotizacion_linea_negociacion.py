# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class TrafitecCotizacionLineaNegociacion(models.Model):
    _name = "trafitec.cotizacion.linea.negociacion"
    _description = "Cotizacion Linea Negociacion"

    tipo = fields.Selection(
        string="Tipo",
        selection=[
            ("con_asociado", "Con asociado"),
            ("con_tiporemolque", "Con tipo de remolque"),
            ("con_asociado_tiporemolque", "Con asociado y tipo de remolque")
        ],
        default="con_asociado",
        required=True
    )
    asociado_id = fields.Many2one(
        "res.partner",
        domain=[
            ("asociado", "=", True)
        ],
        string="Asociado"
    )
    tarifa = fields.Float(
        string="Tarifa para este asociado",
        required=True,
        index=True
    )
    tarifac = fields.Float(
        string="Tarifa para cliente",
        required=True,
        index=True
    )
    detalles = fields.Text(string="Detalles")
    linea_id = fields.Many2one("trafitec.cotizaciones.linea")
    tiporemolque_id = fields.Many2one(
        string="Tipo remolque",
        comodel_name="trafitec.moviles"
    )
    state = fields.Selection(
        string="Estado",
        selection=[
            ("noautorizado", "No autorizado"),
            ("autorizado", "Autorizado")
        ],
        default="noautorizado",
        help="Estado de la negociación."
    )

    @api.constrains("tarifa")
    def _check_tarifa(self):
        for rec in self:
            if rec.tarifa <= 0:
                raise UserError(
                    ("Error !\nLa tarifa debe ser un valor mayor 0")
                )
