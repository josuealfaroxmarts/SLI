# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from xml.dom import minidom


class TrafitecFacturasDocumentos(models.Model):
    _name = "trafitec.facturas.documentos"
    _description = "Facturas Documentos"

    name = fields.Selection(
        string="Tipo",
        selection=[
            ("cartaporte_pdf", "Carta porte PDF"),
            ("cartaporte_xml", "Carta porte XML")
        ],
        required=True,
        default="cartaporte_pdf"
    )
    documento_nombre = fields.Char("Nombre del archivo")
    documento_archivo = fields.Binary(
        string="File",
        required=True
    )
    factura_id = fields.Many2one(
        comodel_name="account.move",
        string="Factura",
        ondelete="cascade"
    )

    @api.constrains("documento_nombre")
    def _check_filename(self):
        for rec in self:
            if rec.documento_archivo:
                if rec.documento_nombre:
                    raise UserError("Alerta..\n No hay archivo.")
                else:
                    tmp = rec.documento_nombre.split(".")
                    ext = tmp[len(tmp) - 1]
                    if ext != "pdf" and rec.name == "cartaporte_pdf":
                        raise UserError(
                            "Alerta..\nSolo se permiten archivos pdf para."
                        )
                    if ext != "xml" and rec.name == "cartaporte_xml":
                        raise UserError(
                            "Alerta..\nSolo se permiten archivos xml para el"
                            + " cfdi."
                        )
