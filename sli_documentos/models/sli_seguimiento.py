## -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, exceptions, tools

from datetime import datetime, date, time, timedelta
import tempfile
import base64
import os

import random

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError, RedirectWarning
#from openerp.exceptions import UserError, RedirectWarning, ValidationError

import ast
import re
from datetime import datetime, date


_logger = logging.getLogger(__name__)

"""
_logger.info('FYI: This is happening')

_logger.warning('WARNING: I don't think you want this to happen!')

_logger.error('ERROR: Something really bad happened!')
"""

class sli_seguimiento_asignar(models.Model):
    _name = 'sli.seguimiento.clasificacion'
    name = fields.Char(string='Nombre', help='Nombre de la clasificación.')
    aplica = fields.Selection(string='Aplica a', selection=[('viaje', 'Viaje'), ('contrarecibo', 'Contra recibo'), ('factura', 'Factura')], default='viaje', help='Indica para que asignación aplica.')


class sli_seguimiento_registro(models.Model):
    _name = 'sli.seguimiento.registro'
    _order = 'id desc'
    
    @api.depends('para_usuario_id', 'viaje_id', 'contrarecibo_id', 'factura_id')
    def compute_nombre(self):
        self.name = (self.para_usuario_id.login or '') + '-' + (self.viaje_id.name or self.contrarecibo_id.name or self.factura_id.name or self.factura_id.number or '')
    
    _rec_name = 'id'
    #name = fields.Char(string='Nombre', compute=compute_nombre, store=True)
    para_usuario_id = fields.Many2one(string='Para', comodel_name='res.users', required=True, help='Usuario al que se asigna el documento.')
    viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes', help='Viaje relacionado.')
    contrarecibo_id = fields.Many2one(string='Contra recibo', comodel_name='trafitec.contrarecibo', help='Contra recibo relacionado.')
    factura_id = fields.Many2one(string='Factura', comodel_name='account.move', help='Factura relacionada.')
    tipo = fields.Selection(string='Tipo', selection=[('viaje', 'Viaje'), ('contrarecibo', 'Contra recibo'), ('factura', 'Factura')], default='viaje', required=True)
    clasificacion_id = fields.Many2one(string='Clasificación', comodel_name='sli.seguimiento.clasificacion', help='Clasificación.')
    detalles = fields.Text(string='Detalles', default='', help='Detalles generales')
    fechahora_ar = fields.Datetime(string='Fecha y hora', help='Fecha y hora de aceptación o rechazo de la asignación.')
    state = fields.Selection(string='Estado', selection=[('enespera', 'En espera'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado'), ('descartado', 'Descartado')], default='enespera', help='Estado de la asignación')
    
    def action_asignar(self):
        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_viaje_form').id
        return {
            'name': _('Asignar'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            #'res_id': self.ids[0],
            'context': {}
        }
    
    
    def action_aceptar(self):
        if self.para_usuario_id.id != self.env.user.id:
            raise UserError(_("Para poder aceptar la asignación debe ser el usuario al que se asigno."))

        #self.fechahora_ar = datetime.now()
        #self.state = 'aceptado'
        self.write({'fechahora_ar': datetime.now(), 'state': 'aceptado'})
        
        if self.tipo == 'viaje':
            #self.viaje_id.asignadoa_id = self.para_usuario_id.id
            #self.viaje_id.asignadoi_id = False
            self.viaje_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoa_id': self.para_usuario_id.id,
                'asignadoi_id': False
            })

        if self.tipo == 'contrarecibo':
            #self.contrarecibo_id.asignadoa_id = self.para_usuario_id.id
            #self.contrarecibo_id.asignadoi_id = False
            self.contrarecibo_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoa_id': self.para_usuario_id.id,
                'asignadoi_id': False
            })

        if self.tipo == 'factura':
            #self.factura_id.asignadoa_id = self.para_usuario_id.id
            #self.factura_id.asignadoi_id = False
            self.factura_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoa_id': self.para_usuario_id.id,
                'asignadoi_id': False
            })

    
    def action_rechazar(self):
        if self.para_usuario_id.id != self.env.user.id:
            raise UserError(_("Para poder rechazar la asignación debe ser el usuario al que se asigno."))
            
        #self.fechahora_ar = datetime.now()
        #self.state = 'rechazado'
        self.write({'fechahora_ar': datetime.now(), 'state': 'rechazado'})
    
        if self.tipo == 'viaje':
            #self.viaje_id.asignadoi_id = False
            #self.viaje_id.asignacion_id = False
            self.viaje_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoi_id': False,
                'asignacion_id': False
            })
    
        if self.tipo == 'contrarecibo':
            #self.contrarecibo_id.asignadoi_id = False
            #self.contrarecibo_id.asignacion_id = False
            self.contrarecibo_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoi_id': False,
                'asignacion_id': False
            })

    
        if self.tipo == 'factura':
            self.factura_id.asignadoi_id = False
            self.factura_id.asignacion_id = False
            self.factura_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).sudo().write({
                'asignadoi_id': False,
                'asignacion_id': False
            })
            


class sli_seguimiento_asignar_viaje(models.TransientModel):
    _name = 'sli.seguimiento.asignar'
    para_usuario_id = fields.Many2one(string='Para', comodel_name='res.users', required=True, help='Usuario al que se asigna el documento.')
    viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes', help='Usuario al que se asigna el documento.')
    contrarecibo_id = fields.Many2one(string='Contra recibo', comodel_name='trafitec.contrarecibo', help='Contrarecibo relacionado.')
    factura_id = fields.Many2one(string='Factura', comodel_name='account.move', help='Factura relacionada.')
    clasificacion_id = fields.Many2one(string='Motivo', comodel_name='sli.seguimiento.clasificacion', required=True, help='Clasificación.')
    tipo = fields.Selection(string='Tipo', selection=[('viaje', 'Viaje'), ('contrarecibo', 'Contra recibo'), ('factura', 'Factura')], default='viaje', required=True)
    detalles = fields.Text(string='Detalles', default='', help='Detalles generales')
    state = fields.Selection(string='Estado', selection=[('enespera', 'En espera'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')], default='enespera', help='Estado de la asignación')

    def enviar_correo(self, asunto='', contenido='', para='', para2=''):
        valores = {
            'subject': asunto,
            'body_html': contenido,
            'email_to': para,
            'email_cc': para2,
            'email_from': 'info@sli.mx',
        }
        #create_and_send_email = self.env['mail.mail'].create(valores).send()
        nuevo = self.env['mail.mail'].create(valores)
        _logger.info("---EMAIL: "+str(nuevo))

    def action_asignar(self):
        correo_titulo = 'Intento de asignación de documento'
        correo_mensaje = ''
        
        viajes_obj = self.env['trafitec.viajes']
        contrarecibos_obj = self.env['trafitec.contrarecibo']
        facturas_obj = self.env['account.move']
        
        registro_obj = self.env['sli.seguimiento.registro']
        
        nuevo = {
            'para_usuario_id': self.para_usuario_id.id,
            'viaje_id': (self.viaje_id.id or False),
            'contrarecibo_id': (self.contrarecibo_id.id or False),
            'factura_id': (self.factura_id.id or False),
            'clasificacion_id': self.clasificacion_id.id,
            'detalles': self.detalles,
            'tipo': self.tipo,
            'state': 'enespera'
        }
        nuevo = registro_obj.create(nuevo)
    
        if self.tipo == 'viaje':
            viaje_dat = viajes_obj.search([('id', '=', self.viaje_id.id)])
            #viaje_dat.asignadoa_id = self.para_usuario_id.id
            #viaje_dat.asignadoi_id = self.para_usuario_id.id
            #viaje_dat.asignacion_id = nuevo.id
            
            self.viaje_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).write({'asignadoi_id': self.para_usuario_id.id, 'asignacion_id': nuevo.id})
            correo_titulo += ' (Viaje {})'.format((viaje_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar el viaje con folio: {} por el motivo: {} Detalles: {}.'.format((viaje_dat.name or ''), self.clasificacion_id.name, self.detalles)

        if self.tipo == 'contrarecibo':
            contrarecibos_dat = contrarecibos_obj.search([('id', '=', self.contrarecibo_id.id)])
            #contrarecibos_dat.asignadoa_id = self.para_usuario_id.id
            #contrarecibos_dat.asignadoi_id = self.para_usuario_id.id
            #contrarecibos_dat.asignacion_id = nuevo.id
            self.contrarecibo_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).write({'asignadoi_id': self.para_usuario_id.id, 'asignacion_id': nuevo.id})

            correo_titulo += ' (Contra recibo {})'.format((contrarecibos_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar el contra recibo con folio: {} por el motivo: {} Detalles: {}.'.format((contrarecibos_dat.name or ''), self.clasificacion_id.name, self.detalles)

        if self.tipo == 'factura':
            facturas_dat = facturas_obj.search([('id', '=', self.factura_id.id)])
            #facturas_dat.asignadoa_id = self.para_usuario_id.id
            #facturas_dat.asignadoi_id = self.para_usuario_id.id
            #facturas_dat.asignacion_id = nuevo.id
            #.with_context(validar_credito_cliente=False)
            self.factura_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).write({'asignadoi_id': self.para_usuario_id.id, 'asignacion_id': nuevo.id})
            correo_titulo += ' (Factura {})'.format((facturas_dat.number or facturas_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar la factura con folio: {} por el motivo: {} Detalles: {}.'.format((facturas_dat.number or facturas_dat.name or ''), self.clasificacion_id.name, self.detalles)
        
        
        #Notificar.
        self.enviar_correo(asunto=correo_titulo, contenido=correo_mensaje, para=self.para_usuario_id.login)
        

class sli_seguimiento_viajes(models.Model):
    _inherit = 'trafitec.viajes'
    asignadoi_id = fields.Many2one(string='Intentando asignar a', comodel_name='res.users', help='Usuario al que se intenta asignar el viaje.')
    asignacion_id = fields.Many2one(string='Asignación', comodel_name='sli.seguimiento.registro', help='Asignación')

    
    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        # sli_seguimeinto_asignar_viaje_form
        #if not self.asignadoa_id:
        #    raise UserError(_("El viaje no esta asignado."))
        if self.asignacion_id:
            self.asignacion_id.state = 'descartado'
            self.asignacion_id.fechahora_ar = datetime.now()
            
        self.with_context(validar_credito_cliente=False).write({'asignacion_id': False, 'asignadoa_id': False, 'asignadoi_id': False})
        #self.asignacion_id = False
        #self.asignadoa_id = False
        #self.asignadoi_id = False

    
    def action_intento_quitar(self):
        """Quita la asignacion incondicionalmente."""
        # sli_seguimeinto_asignar_viaje_form
        # if not self.asignadoa_id:
        #    raise UserError(_("El viaje no esta asignado."))
        if self.asignacion_id:
            self.asignacion_id.state = 'descartado'
            self.asignacion_id.fechahora_ar = datetime.now()
    
        self.asignacion_id = False
        self.asignadoa_id = False
        self.asignadoi_id = False

    
    def action_asignar_asignar(self):
        """Asignación."""
        if self.asignadoa_id:
            if self.asignadoa_id.id != self.env.user.id:
                raise UserError(_('Para poder asignar el viaje, este viaje debe estar asignado a usted.'))

        if self.asignadoi_id:
           raise UserError(_('Para poder asignar el viaje no debe haber intento de asignación.'))

        
        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_viaje_form').id
        viaje_id = self.id
        
        return {
            'name': _('Asignar viaje '+(self.name or '')),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            #'res_id': self.ids[0],
            'context': {'default_viaje_id': viaje_id, 'default_tipo': 'viaje'}
        }
    
class sli_seguimiento_contrarecibos(models.Model):
    _inherit = 'trafitec.contrarecibo'
    asignadoa_id = fields.Many2one(string='Asignado a', comodel_name='res.users', help='Usuario que tiene asignado el contra recibo.')
    asignadoi_id = fields.Many2one(string='Intentando asignar a', comodel_name='res.users', help='Usuario al que se intenta asignar el contra recibo.')
    asignacion_id = fields.Many2one(string='Asignación', comodel_name='sli.seguimiento.registro', help='Asignación')

    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        # sli_seguimeinto_asignar_viaje_form
        #if not self.asignadoa_id:
        #    raise UserError(_("El contra recibo no esta asignado."))
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
            #'res_id': self.ids[0],
            'context': {'default_contrarecibo_id': contrarecibo_id, 'default_tipo': 'contrarecibo'}
        }

class sli_seguimiento_facturas(models.Model):
    _inherit = 'account.move'
    asignadoa_id = fields.Many2one(string='Asignado a', comodel_name='res.users', help='Usuario que tiene asignada la factura.')
    asignadoi_id = fields.Many2one(string='Intentando asignar a', comodel_name='res.users', help='Usuario al que se intenta asignar la factura.')
    asignacion_id = fields.Many2one(string='Asignación', comodel_name='sli.seguimiento.registro', help='Asignación')

    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        # sli_seguimeinto_asignar_viaje_form
        #if not self.asignadoa_id:
        #    raise UserError(_("La factura no esta asignado."))
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
                raise UserError(_('Para poder asignar la factura, esta factura debe estar asignado a usted.'))
            
        if self.asignadoi_id:
           raise UserError(_('Para poder asignar la factura no debe haber intento de asignación.'))

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
            #'res_id': self.ids[0],
            'context': {'default_factura_id': factura_id, 'default_tipo': 'factura'}
        }

 