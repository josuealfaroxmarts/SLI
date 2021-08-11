# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class trafitec_viaje_cambiartarifa_wizard(models.TransientModel):
    _name = 'trafitec.viaje.cambiartarifa.wizard'
    _description = 'viaje cambiar tarifa wizard'
    
    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    tarifa = fields.Float(string='Tarifa', default=_get_tarifa, required=True)
    
    def _get_viajeid(self):
        viajes_obj = self.env['trafitec.viajes'].search([
                ('id', '=', self._context.get('active_id'))
            ],
            limit=1
        )
        return viajes_obj

    def _get_tarifa(self):
        viajes_obj = self.env['trafitec.viajes'].search([
                ('id', '=', self._context.get('active_id'))
            ],
            limit=1
        )
        return viajes_obj.tarifa_cliente

    def action_cambiartarifa(self):
        self.ensure_one()
        for line in self:
            line.viaje_id.with_context(validar_tc=True).write({
                'tarifa_cliente': line.tarifa
            })