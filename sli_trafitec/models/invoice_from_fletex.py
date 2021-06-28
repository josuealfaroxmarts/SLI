# -*- coding: utf-8 -*-

from openerp import _, api, fields, models, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


class trafitec_invoice_fletex(models.Model):
    _name = 'invoice.from.fletex'
    _rec_name = 'fletexShipmentReference'

    clientId = fields.Many2one('res.partner', string='Asociado', required=True)
    shipmentId = fields.Many2one(
        'trafitec.viajes', string="Folio Viaje", required=True)
    fletexProjectReference = fields.Char(string="Referencia Projecto Fletex")
    fletexShipmentReference = fields.Char(string="Referencia Viaje Fletex")
    invoiceXmlName = fields.Char(compute="changeNameAttachment")
    invoiceXml = fields.Binary(string="Factura XML")
    invoicePdfName = fields.Char(compute="changeNameAttachment")
    invoicePdf = fields.Binary(string="Factura PDF")

    @api.depends('shipmentId')
    
    def changeNameAttachment(self):
        if self.shipmentId:
            self.invoicePdfName = "Factura PDF del viaje ({}).pdf".format(
                self.shipmentId.name)
            self.invoiceXmlName = "Factura XML del viaje ({}).xml".format(
                self.shipmentId.name)
