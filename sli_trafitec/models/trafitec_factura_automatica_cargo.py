# -*- coding: utf-8 -*-

from odoo import models, fields


class TrafitecFacturaAutomaticaCargo(models.Model):
    _name = "trafitec.factura.automatica.cargo"
    _description = "Factura Automatica Cargo"

    name = fields.Many2one(
        "trafitec.tipo.cargos.adicionales",
        string="Producto",
        required=True,
        readonly=True
    )
    valor = fields.Float(
        string="Total",
        required=True,
        readonly=True
    )
    line_cargo_id = fields.Many2one(
        "trafitec.facturas.automaticas",
        string="ID factura automatica"
    )
