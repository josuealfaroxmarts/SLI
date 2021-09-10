# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TrafitecCrmTraficoResultadoWizard(models.TransientModel):
    _name = "trafitec.crm.trafico.resultado.wizard"
    _description = "CRM Trafico Resultado Wizard"

    crm_trafico_id = fields.Many2one(
        string="",
        comodel_name="trafitec.crm.trafico.wizard"
    )
    viaje_id = fields.Many2one(
        string="Viaje",
        comodel_name="trafitec.viajes"
    )
    fecha = fields.Char(string="Fecha")
    origen = fields.Char(string="Origen")
    destino = fields.Char(string="Destino")
    producto = fields.Char(string="Producto")
    asociado = fields.Char(string="Asociado")
    tarifa_a = fields.Float(string="Tarifa")
    cliente = fields.Char(string="Cliente")
    peso = fields.Float(string="Peso")
    estado = fields.Char(string="Estado")
