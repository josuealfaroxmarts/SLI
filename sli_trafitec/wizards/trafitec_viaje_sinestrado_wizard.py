# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class trafitec_viaje_sinestrado(models.TransientModel):
    _name = 'trafitec.viaje.sinestrado.wizard'
    _description = 'viajes sinestrado'

    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    motivo = fields.Text(string='Motivo de siniestro')

    def _get_viajeid(self):
        viajes_obj = self.env['trafitec.viajes'].search([
            ('id', '=', self._context.get('active_id'))
        ])
        if viajes_obj.en_contrarecibo:
            raise UserError(_(
                "El viaje seleccionado ya tiene contra recibo."
            ))
        if viajes_obj.en_factura:
            raise UserError(_("El viaje seleccionado ya tiene factura."))
        if viajes_obj.en_cp:
            raise UserError(_("El viaje seleccionado ya tiene carta porte."))
        return viajes_obj

    def siniestrado_button(self):
        self.ensure_one()
        for line in self:
            line.viaje_id.write({
                'motivo_siniestrado': line.motivo,
                'state': 'Siniestrado',
                'fecha_cambio_estado': datetime.datetime.now()
            })