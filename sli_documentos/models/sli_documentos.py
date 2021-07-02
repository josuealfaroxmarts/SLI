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


class sli_documentos_documentos(models.Model):
    _name = 'sli.documentos.documentos'
    
    
    @api.depends('fecha_final')
    def compute_dias_para_vencimiento(self):
        hoy = date.today()
        fecha_final = datetime.strptime(self.fecha_final, "%Y-%m-%d").date()
        dif = fecha_final - hoy
        self.dias_para_vencimiento = dif.days
    
    name = fields.Char(string='Nombre', help='Nombre del documento')
    folio = fields.Char(string='Folio', help='Folio del documento')
    fecha = fields.Date(string='Fecha del documento', help='Fecha del documento.')
    persona_id = fields.Many2one(string='Persona relacionada', comodel_name='res.partner', help='Persona relacionada.')
    empleado_id = fields.Many2one(string='Empleado relacionado', comodel_name='hr.employee', help='Empleado relacionado.')
    vehiculo_id = fields.Many2one(string='Vehiculo relacionado', comodel_name='fleet.vehicle', help='Vehiculo relacionado.')
    fecha_inicial = fields.Date(string='Fecha inicial de documento', help='Fecha de vigencia inicial del documento.')
    fecha_final = fields.Date(string='Fecha final de documento', help='Fecha de vigencia final del documento.')
    detalles = fields.Text(string='Detalles del documento', help='Detalles especificos del documento')
    tipo = fields.Selection(string='Tipo', selection=[('noespecificado', '(No especificado)'), ('licencia', 'Licencia'), ('contrato', 'Contrato'), ('otro', 'Otro')], default='noespecificado')
    personas_ids = fields.One2many(string='Personas a notificar', comodel_name='sli.documentos.personas', inverse_name='documento_id', help='Personas relacionadas a notificar')
    version = fields.Integer(string='Versión', default=1, help='Versión del documento.')
    notificar_dias = fields.Integer(string='Notificar faltando', default=7, help='Indica los dias en que se iniciaran las notificaciones antes de la fecha final')
    notificar_frecuencia = fields.Integer(string='Notificar frecuencia', default=1, help='Frecuencia de notificaciones.')
    notificar_fechahorau = fields.Datetime(string='Notificar fecha y hora de ultima notificacion', help='Fecha y hora de ultima notificacion.')
    state = fields.Selection(string='Estado', selection=[('vigente', 'Vigente'), ('vencido', 'Vencido')], default='vigente', help='Indica el estado del documento establecido manualmente.')
    dias_para_vencimiento = fields.Integer(string='Días para vencimiento', compute=compute_dias_para_vencimiento, store=True, help='Días para vencimiento.')
    active = fields.Boolean(string='Activo', default=True)
    
    archivo_nombre = fields.Char("Nombre archivo", default='datos.txt')
    archivo_datos = fields.Binary()
    
    
    def action_servicio_notificaciones(self):
        #Obtener todos los documentos vigentes.
        documentos = self.env['sli.documentos.documentos'].search([('state', '=', 'vigente')])
        
        dias = 0
        dias_un = 0
        hoy = None
        notificar = False
        
        #Buscar documentos proximos a vencer.
        for d in documentos:
            dias = 0
            dias_un = 0
            notificar = False
            
            hoy = date.today()
            fecha_final = datetime.strptime(d.fecha_final, "%Y-%m-%d").date()
            dif = fecha_final - hoy
            dias = dif.days

            #Actualiza el estado del documento.
            if dias <= 0:
                d.state = 'vencido'
                continue
            
            #Verifica si esta por vencer.
            if dias <= d.notificar_dias:
                if d.notificar_fechahorau:
                    fecha_final_un = datetime.strptime(d.notificar_fechahorau, "%Y-%m-%d %H:%M:%S").date()
                    dif_un = hoy - fecha_final_un
                    dias_un = dif_un.days
                   
                    if dias_un >= 1:
                        notificar = True
                else:
                    notificar = True
               
                #Notificar.
                if notificar:
                    #Establece la fecha u hora de ultima notificación.
                    d.notificar_fechahorau = datetime.now()
                    
                    #Enviar mensaje.
                    mensaje = "Faltan {} dias para vencimiento de {} con folio {}.".format(dias, d.name, d.folio)
                    for p in d.personas_ids:
                        #d.detalles = (d.detalles or '') + '/' + (mensaje or '')
                        if p.persona_id.email:
                            self.enviar_correo(asunto="Vigencia", contenido=mensaje, para=(p.persona_id.email or ''))
                            print("Notificar:")
        
        
    def enviar_correo(self, asunto='', contenido='', para='', para2=''):
        valores = {
            'subject': asunto,
            'body_html': contenido,
            'email_to': para,
            'email_cc': para2,
            'email_from': 'info@sli.mx',
        }
        #create_and_send_email = self.env['mail.mail'].create(valores).send()
        create_and_send_email = self.env['mail.mail'].create(valores)

    
    def create(self, vals):
        nuevo = super(sli_documentos_documentos, self).create(vals)
        return nuevo

    @api.constrains('notificar_dias', 'notificar_frecuencia')
    def valida(self):
        error = False
        errores = ''
        
        if not self._context.get('validar', True):
            return
        
        
        #Validaciones.
        if self.fecha_inicial > self.fecha_final:
            error = True
            errores += "La fecha inicial debe ser menor a la fecha final.\n"
        
        if self.notificar_dias <= 0:
            error = True
            errores += 'Los dias para la notificación debe ser mayor a cero.\n'

        if self.notificar_frecuencia <= 0:
            error = True
            errores += 'La frecuencia para la notificación debe ser mayor a cero.\n'
        
        
        if error:
            raise UserError(_(errores))

class sli_documentos_personas(models.Model):
    _name = 'sli.documentos.personas'
    documento_id = fields.Many2one(string='Documento', comodel_name='sli.documentos.documentos', help='Documento relacionado')
    persona_id = fields.Many2one(string='Persona', comodel_name='res.partner', help='Persona relacionada')
