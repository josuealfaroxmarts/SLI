# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class TrafitecFacturaLineaComision(models.Model):
    _name = "trafitec.factura.linea.comision"
    _description = "Factura Linea Comision"

    name = fields.Char(
        string="Folio del viaje", 
        readonly=True
    )
    fecha = fields.Date(
        string="Fecha", 
        readonly=True
    )
    comision = fields.Float(
        string="Comision", 
        readonly=True
    )
    abonos = fields.Float(
        string="Abonos", 
        readonly=True
    )
    saldo = fields.Float(
        string="Saldo", 
        readonly=True
    )
    asociado_id = fields.Many2one(
        "res.partner",
        string="Asociado",
        domain="[("asociado","=",True)]",
        readonly=True
    )
    tipo_viaje = fields.Char(
        string="Tipo de viaje", 
        readonly=True
    )
    cargo_id = fields.Many2one(
        "trafitec.cargos", 
        string="ID comision"
    )
    line_id = fields.Many2one(
        comodel_name="trafitec.facturas.comision",
        string="ID contrarecibo",
        ondelete="cascade"
    )
    viaje_id = fields.Many2one(
        "trafitec.viajes", 
        string="ID viaje"
    )
