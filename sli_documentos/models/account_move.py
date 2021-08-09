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

class AccountMove(models.Model):
    _inherit = 'account.move'

    asignadoa_id = fields.Many2one(
        string='Asignado a', 
        comodel_name='res.users',
         help='Usuario que tiene asignada la factura.'
    )
    asignadoi_id = fields.Many2one(
        string='Intentando asignar a', 
        comodel_name='res.users', 
        help='Usuario al que se intenta asignar la factura.'
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
                raise UserError(_
                ('Para poder asignar la factura, esta factura debe estar asignado a usted.'))
            
        if self.asignadoi_id:
           raise UserError(_
           ('Para poder asignar la factura no debe haber intento de asignación.'))

        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_factura_form').id
        factura_id = self.id
        
        return {
            'name': _('Asignar factura '+(self.number or '')),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': {'default_factura_id': factura_id, 'default_tipo': 'factura'}
        }