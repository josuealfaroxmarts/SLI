from odoo import models, fields, api, exceptions, tools

from datetime import datetime, date, time, timedelta
import tempfile
import base64
import os

import random

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError, RedirectWarning

import ast
import re
from datetime import datetime, date


class TrafitecContrarecibo(models.Model):
    _inherit = 'trafitec.contrarecibo'
    
    asignadoa_id = fields.Many2one(
        string='Asignado a', 
        comodel_name='res.users', 
        help='Usuario que tiene asignado el contra recibo.'
    )
    asignadoi_id = fields.Many2one(
        string='Intentando asignar a', 
        comodel_name='res.users', 
        help='Usuario al que se intenta asignar el contra recibo.'
    )
    asignacion_id = fields.Many2one(
        string='Asignación', 
        comodel_name='sli.seguimiento.registro', 
        help='Asignación'
    )

    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        if self.asignacion_id:
            self.asignacion_id.state = 'descartado'
            self.asignacion_id.fechahora_ar = datetime.now()

        self.asignacion_id = False
        self.asignadoa_id = False
        self.asignadoi_id = False

        self.asignadoa_id = False

    
    def action_asignar_asignar(self):
        """Asignación."""
        if self.asignadoa_id:
            if self.asignadoa_id.id != self.env.user.id:
                raise UserError(_('Para poder asignar el contra recibo, este contra recibo debe estar asignado a usted.'))
        
        if self.asignadoi_id:
           raise UserError(_('Para poder asignar el contra recibo no debe haber intento de asignación.'))

           
        
        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_contrarecibo_form').id
        contrarecibo_id = self.id
        
        return {
            'name': _('Asignar contra recibo '+(self.name or '')),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': {'default_contrarecibo_id': contrarecibo_id, 'default_tipo': 'contrarecibo'}
        }