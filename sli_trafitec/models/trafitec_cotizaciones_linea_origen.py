# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class TrafitecCotizacionesLineaOrigen(models.Model):
    _name = "trafitec.cotizaciones.linea.origen"
    _description = "Cotizaciones Linea Origen"

    name = fields.Char(
        string="Folio",
        readonly=True
    )
    origen = fields.Many2one(
        "trafitec.ubicacion",
        string="Ubicación origen",
        required=True
    )
    destino = fields.Many2one(
        "trafitec.ubicacion",
        string="Ubicación destino",
        required=True
    )
    cantidad = fields.Float(
        string="Cantidad",
        required=True
    )
    facturar = fields.Boolean(
        string="Facturar",
        default=True
    )
    psf = fields.Boolean(string="PSF")
    csf = fields.Boolean(string="CSF")
    linea_id = fields.Many2one(
        "trafitec.cotizaciones.linea",
        ondelete="restrict"
    )
    folio_cotizacion = fields.Char(
        string="No. de cotización",
        related="linea_id.cotizacion_id.name",
        readonly=True,
        store=True
    )
    cliente_cotizacion = fields.Many2one(
        "res.partner",
        related="linea_id.cotizacion_id.cliente",
        readonly=True,
        store=True
    )
    state = fields.Selection(
        [
            ("disponible", "Disponible"),
            ("en_espera", "En espera"),
            ("cancelada", "Cancelada"),
            ("cerrada", "Cerrada")
        ],
        string="Estado",
        default="disponible"
    )

    @api.depends(
        "name",
        "folio_cotizacion",
        "cliente_cotizacion",
        "origen",
        "destino"
    )
    def name_get(self):
        result = []
        name = ""
        for rec in self:
            if (
                rec.name
                and rec.folio_cotizacion
                and rec.cliente_cotizacion
                and rec.origen
                and rec.destino
            ):
                name = (
                    (rec.folio_cotizacion or "")
                    + "/"
                    + (rec.name or "")
                    + "/"
                    + (rec.cliente_cotizacion.name or "")
                    + "/"
                    + (rec.origen.name or "")
                    + "/"
                    + (rec.destino.name or "")
                )
                result.append((rec.id, name))
            elif (
                rec.name
                and rec.folio_cotizacion
                and rec.origen
                and rec.destino
                and not rec.cliente_cotizacion
            ):
                name = (
                    (rec.folio_cotizacion or "")
                    + "/"
                    + (rec.name or "")
                    + "/"
                    + (rec.origen.name or "")
                    + "/"
                    + (rec.destino.name or "")
                )
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=10):
        args = args or []
        domain = []
        if not (name == "" and operator == "ilike"):
            args += [
                "|",
                "|",
                "|",
                "|",
                ("name", "ilike", name),
                ("linea_id.cotizacion_id.name", "ilike", name),
                ("linea_id.cotizacion_id.cliente.name", "ilike", name),
                ("origen.name", "ilike", name),
                ("destino.name", "ilike", name)
            ]
        result = self.search(domain + args, limit=limit)
        res = result.name_get()
        return res

    @api.constrains("cantidad")
    def _check_cantidad(self):
        for rec in self:
            if rec.cantidad <= 0:
                raise UserError(
                    ("Error !\nEn la cantidad debe ser un valor mayor 0")
                )

    @api.model
    def create(self, vals):
        if "company_id" in vals:
            vals["name"] = self.env["ir.sequence"].with_context(
                force_company=vals["company_id"]
            ).next_by_code("Trafitec.Cotizaciones.Linea.Origen") or ("Nuevo")
        else:
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "Trafitec.Cotizaciones.Linea.Origen"
            ) or ("Nuevo")
        return super(TrafitecCotizacionesLineaOrigen, self).create(vals)
