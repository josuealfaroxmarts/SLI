# -*- coding: utf-8 -*-

from odoo import api, fields, models


class RoutersShipments(models.Model):
    _name = "trafitec.routers"
    _description = "Rutas de los viajes realizados en FLETEX"

    shipment_id_fletex = fields.Char(string="ID Viaje asociado",)
    shipment_id_odoo = fields.Many2one(
        "trafitec.viajes",
        string="Viaje",
    )
    associated_id = fields.Many2one(
        "res.partner",
        string="Asociado",
    )
    quotation_id = fields.Many2one(
        "trafitec.cotizacion",
        string="Cotización",
    )
    google_maps = fields.Char(string="Google Maps")

    @api.onchange()
    def change_data(self):
        self.associated_id = self.shipment_id_odoo.asociado_id.id
        self.quotation_id = self.shipment_id_odoo.linea_id.id
        origin_latitude = self.shipment_id_odoo.origen.latitud
        origin_lenght = self.shipment_id_odoo.origen.longitud
        destination_latitude = self.shipment_id_odoo.destino.latitud
        destination_lenght = self.shipment_id_odoo.destino.longitud
        self.google_maps = "https://www.google.com/maps/dir/{},{}/{},{}/?hl=es".format(
            origin_latitude, origin_lenght, destination_latitude, destination_lenght)

    @api.constrains()
    def change_data(self):
        self.associated_id = self.shipment_id_odoo.asociado_id.id
        self.quotation_id = self.shipment_id_odoo.linea_id.id
        origin_latitude = self.shipment_id_odoo.origen.latitud
        origin_lenght = self.shipment_id_odoo.origen.longitud
        destination_latitude = self.shipment_id_odoo.destino.latitud
        destination_lenght = self.shipment_id_odoo.destino.longitud
        self.google_maps = "https://www.google.com/maps/dir/{},{}/{},{}/?hl=es".format(
            origin_latitude, origin_lenght, destination_latitude, destination_lenght)
