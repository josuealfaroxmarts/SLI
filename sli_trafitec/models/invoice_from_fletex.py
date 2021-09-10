# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools


class InvoiceFromFletex(models.Model):
    _name = "invoice.from.fletex"
    _description = "Invoice From Fletex"
    _rec_name = "fletexShipmentReference"

    clientId = fields.Many2one(
        "res.partner",
        string="Asociado",
        required=True
    )
    shipmentId = fields.Many2one(
        "trafitec.viajes",
        string="Folio Viaje",
        required=True
    )
    fletexProjectReference = fields.Char(string="Referencia Projecto Fletex")
    fletexShipmentReference = fields.Char(string="Referencia Viaje Fletex")
    invoiceXmlName = fields.Char(compute="changeNameAttachment")
    invoiceXml = fields.Binary(string="Factura XML")
    invoicePdfName = fields.Char(compute="changeNameAttachment")
    invoicePdf = fields.Binary(string="Factura PDF")

    @api.depends("shipmentId")
    def changeNameAttachment(self):
        for rec in self:
            if rec.shipmentId:
                rec.invoicePdfName = "Factura PDF del viaje ({}).pdf".format(
                    rec.shipmentId.name)
                rec.invoiceXmlName = "Factura XML del viaje ({}).xml".format(
                    rec.shipmentId.name)
