# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime

_logger = logging.getLogger(__name__)


class trafitec_cotizacion_cancelar(models.TransientModel):
    _name = 'trafitec.cotizacion.cancelar.wizard'
    _description='cotizacion cancelar wizard'
    def _get_cotizacionid(self):
        print(self._context.get('active_id'))
        cotizacion_obj = self.env['trafitec.cotizacion'].search([('id', '=', self._context.get('active_id'))])
        return cotizacion_obj

    cotizacion_id = fields.Many2one('trafitec.cotizacion', default=_get_cotizacionid)
    motivo = fields.Text(string='Motivo')

    
    def cancelacion_button(self):
        self.ensure_one()
        for line in self:
            line.cotizacion_id.write(
                {'motivo_cancelacion': line.motivo, 'state': 'Cancelada', 'fecha_cancelacion': datetime.datetime.now()})
            
            sale_order_obj = self.env['sale.order']
            sale_order_dat = sale_order_obj.search([('id', '=', line.cotizacion_id.odoo_cotizacion_id.id)], limit=1)
            if len(sale_order_dat) > 0:
                sale_order_dat.with_context(trafitec_cancelar=True).action_cancel()