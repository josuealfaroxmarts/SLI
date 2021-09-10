# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class TrafitecViajeCargos(models.Model):
    _name = "trafitec.viaje.cargos"
    _description = "Viaje Cargos"

    name = fields.Many2one(
        "trafitec.tipo.cargos.adicionales",
        string="Tipos de cargos adicionales",
        required=True
    )
    valor = fields.Float(
        string="Valor", 
        required=True
    )
    line_cargo_id = fields.Many2one(
        "trafitec.viajes", 
        string="ID viaje"
    )
    sistema = fields.Boolean(
        string="Sistema", 
        default=False
    )
    validar_en_cr = fields.Boolean(
        string="Validar en CR",
        related="name.validar_en_cr"
    )
    tipo = fields.Selection(
        [
            ("pagar_cr_cobrar_f", "Pagar en contrarecibo y cobrar en factura cliente"),
            ("pagar_cr_nocobrar_f", "Pagar en contrarecibo y no cobrar en factura cliente"),
            ("nopagar_cr_cobrar_f", "No pagar en contrarecibo y cobrar en factura cliente")
        ],
        string="Tipo",
        default="pagar_cr_cobrar_f",
        required=True
    )