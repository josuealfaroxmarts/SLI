# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class TrafitecCargosXAbonos(models.Model):
    _name = "trafitec.cargos.x.abonos"
    _description = "Abonos Cargos X"

    cargosx_id = fields.Many2one(
        comodel_name="trafitec.cargos.x",
        string="Cargo",
        required=True
    )
    abono = fields.Float(
        string="Abono",
        default=0,
        required=True
    )
    generadoen = fields.Selection(
        string="Generado en",
        selection=[
            ("sistema", "Sistema"),
            ("manual", "Manual"),
            ("contrarecibo", "Contra recibo"),
            ("factura", "Factura")
        ],
        default="sistema"
    )
    observaciones = fields.Text(
        string="Observaciones",
        required=True,
        help="Observaciones del abono."
    )
