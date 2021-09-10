# -*- coding: utf-8 -*-

from odoo import models, fields


class TrafitecCotizacionesDocumentos(models.Model):
    _name = "trafitec.cotizaciones.documentos"
    _description = "Cotizaciones Documentos"

    cotizacion_id = fields.Many2one(
        string="Cotización",
        comodel_name="trafitec.cotizacion",
        help="Cotización."
    )
    tipodocumento_id = fields.Many2one(
        string="Tipo de documento",
        comodel_name="trafitec.tipo.doc",
        required=True,
        help="Tipo de documento."
    )
    tipo_tipo = fields.Selection(
        string="Tipo",
        related="tipodocumento_id.tipo"
    )
    tipo_evidencia = fields.Boolean(
        string="Evidencia",
        related="tipodocumento_id.evidencia"
    )
    tipo_dmc = fields.Boolean(
        string="DMC",
        related="tipodocumento_id.dmc"
    )
