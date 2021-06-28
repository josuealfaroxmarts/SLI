## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import xlrd
import shutil
import datetime
from datetime import timedelta
import logging

# from openerp.tools import amount_to_text
from . import amount_to_text

import xlsxwriter
import base64

# from amount_to_text import *


# from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

_logger = logging.getLogger(__name__)


class trafitec_crm_trafico(models.TransientModel):
    _name = 'trafitec.crm.trafico'
    _order = 'id desc'

    name = fields.Char(string='Nombre', default='', required=True)
    buscar_folio = fields.Char(string='Folio')
    buscar_producto = fields.Char(string='Producto')
    buscar_origen = fields.Char(string='Origen')
    buscar_destino = fields.Char(string='Destino')
    buscar_cliente = fields.Char(string='Cliente')
    buscar_asociado = fields.Char(string='Asociado')
    buscar_fechai = fields.Date(string='Fecha inicial', default=datetime.datetime.today() + timedelta(days=-7))
    buscar_fechaf = fields.Date(string='Fecha final', default=datetime.datetime.today())
    buscar_lineanegocio_id = fields.Many2one(string='Línea de negocio', comodel_name='trafitec.lineanegocio', default=1)

    
    def _calculado(self):
        print("--CALCULADO---------------------------------")
        self.name = "AUTOMATICO"
        self.action_buscar_cotizaciones2()

    calculado = fields.Char(string='', compute=_calculado)

    def _viajes_info(self):
        info = ''
        tarifa_minima = 0
        tarifa_maxima = 0
        tarifa_promedio = 0
        tarifa_total = 0

        for v in self.resultados_id:
            tarifa_total += v.tarifa_a
            if v.tarifa_a > tarifa_maxima:
                tarifa_maxima = v.tarifa_a
            if v.tarifa_a < tarifa_minima:
                tarifa_minima = v.tarifa_a

        tarifa_promedio = tarifa_total / len(self.resultados_id)
        info = "<b>Tarifa mínima:</b>{0:.2f} Tarifa máxima:{0:.2f} Tarifa promedio:{0:.2f}".format(tarifa_minima,
                                                                                                   tarifa_maxima,
                                                                                                   tarifa_promedio)
        return info

    
    def action_buscar_cotizaciones2(self):
        cotiaciones = []
        filtro = []
        self.cotizaciones_abiertas_id = None

        filtro.append(('linea_id.cotizacion_id.state', '=', 'Disponible'))
        filtro.append(('linea_id.cotizacion_id.mostrar_en_crm_trafico', '=', True))
        filtro.append(('linea_id.cotizacion_id.lineanegocio', '!=', 3))  # No mostrar contenedores.
        filtro.append(('state', '=', 'Disponible'))  # No mostrar contenedores.

        cotizacion_linea_obj = self.env['trafitec.cotizaciones.linea']
        cotizacion_linea_origen_obj = self.env['trafitec.cotizaciones.linea.origen']
        viajes_obj = self.env['trafitec.viajes']

        cotizacion_linea_origen_dat = cotizacion_linea_origen_obj.search(filtro, limit=1000)

        for clo in cotizacion_linea_origen_dat:
            viajes_dat = viajes_obj.search([('subpedido_id.id', '=', clo.id)])

            totalviajes = 0.0
            for v in viajes_dat:
                totalviajes += v.peso_origen_total / 1000

            cotiaciones.append(
                {
                    'crm_trafico_id': self.id,
                    'folio': clo.linea_id.cotizacion_id.name,
                    'fecha': clo.linea_id.cotizacion_id.fecha,
                    'origen': clo.origen.name,
                    'destino': clo.destino.name,
                    'producto': clo.linea_id.cotizacion_id.product.name,
                    'tarifa_a': clo.linea_id.tarifa_asociado,
                    'cliente': clo.linea_id.cotizacion_id.cliente.name,
                    'usuarios_asignados': reduce(lambda txt, item: txt + '(' + (item.name or '') + ') ', clo.linea_id.cotizacion_id.user_ids, ""),
                    'peso': clo.cantidad,
                    'peso_viajes': totalviajes,
                    'cotizacion_id': clo.linea_id.cotizacion_id.id,
                    'cotizacion_linea_id': clo.linea_id.id,
                    'avance': totalviajes * 100 / clo.cantidad,
                    'detalles': clo.linea_id.detalle_asociado,
                    'semaforo_valor': clo.linea_id.cotizacion_id.semaforo_valor,
                    'lineanegocio': clo.linea_id.cotizacion_id.lineanegocio.name,
                    'estado': clo.linea_id.cotizacion_id.state
                }
            )

        self.cotizaciones_abiertas_id = None
        self.cotizaciones_abiertas_id = cotiaciones

    viajes_info = fields.Html(string='Info', default='', readonly=True)
    resultados_id = fields.One2many(string="Resultado", comodel_name="trafitec.crm.trafico.resultado",
                                    inverse_name="crm_trafico_id")
    cotizaciones_abiertas_id = fields.One2many(string="Cotizaciones", comodel_name="trafitec.crm.trafico.pedidos",
                                               inverse_name="crm_trafico_id")

    
    def action_buscar_viajes(self):
        if not self.buscar_fechai or not self.buscar_fechaf:
            raise UserError(_("Debe especificar el periodo de fechas."))

        viajes = []
        filtro = []
        self.resultados_id = None

        info = ''
        tarifa_minima = 0
        tarifa_maxima = 0
        tarifa_promedio = 0
        tarifa_total = 0

        if self.buscar_folio:
            filtro.append(('name', 'ilike', '%' + self.buscar_folio + '%'))

        if self.buscar_producto:
            filtro.append(('product.name', 'ilike', '%' + self.buscar_producto + '%'))

        if self.buscar_cliente:
            filtro.append(('cliente_id.name', 'ilike', '%' + self.buscar_cliente + '%'))

        if self.buscar_asociado:
            filtro.append(('asociado_id.name', 'ilike', '%' + self.buscar_asociado + '%'))

        if self.buscar_origen:
            filtro.append(('origen.name', 'ilike', '%' + self.buscar_origen + '%'))

        if self.buscar_destino:
            filtro.append(('destino.name', 'ilike', '%' + self.buscar_destino + '%'))

        if self.buscar_lineanegocio_id:
            filtro.append(('lineanegocio', '=', self.buscar_lineanegocio_id.id))

        filtro.append(('fecha_viaje', '>=', self.buscar_fechai))
        filtro.append(('fecha_viaje', '<=', self.buscar_fechaf))

        filtro.append(('state', '=', 'Nueva'))

        viajes_obj = self.env['trafitec.viajes']
        viajes_dat = viajes_obj.search(filtro, limit=1000)

        c = 0
        for v in viajes_dat:
            c += 1
            if c == 1:
                tarifa_minima = v.tarifa_asociado
                tarifa_maxima = v.tarifa_asociado

            tarifa_total += v.tarifa_asociado
            if v.tarifa_asociado > tarifa_maxima:
                tarifa_maxima = v.tarifa_asociado
            if v.tarifa_asociado < tarifa_minima:
                tarifa_minima = v.tarifa_asociado

            viajes.append(
                {
                    'folio': v.name,
                    'fecha': v.fecha_viaje,
                    'origen': v.origen.name,
                    'destino': v.destino.name,
                    'producto': v.product.name,
                    'asociado': v.asociado_id.name,
                    'tarifa_a': v.tarifa_asociado,
                    'cliente': v.cliente_id.name,
                    'viaje_id': v.id,
                    'peso': v.peso_origen_total / 1000,
                    'estado': v.state
                }
            )
        if len(viajes_dat) > 0:
            tarifa_promedio = tarifa_total / len(viajes_dat)
        info = "<b>Tarifa mínima: </b><font color='green'>{0:,.2f}</font> <b>Tarifa máxima</b>: <font color='red'>{1:,.2f}</font> <b>Tarifa promedio: </b>{2:,.2f}".format(
            tarifa_minima, tarifa_maxima, tarifa_promedio)

        self.viajes_info = info
        self.resultados_id = None
        self.resultados_id = viajes

    @api.model
    def retrieve_sales_dashboard(self):
        """ Fetch data to setup Sales Dashboard """
        result = {'meeting': {'today': 0, 'next_7_days': 4.5, },
                  'activity': {'today': 0, 'overdue': 0, 'next_7_days': 4, },
                  'closing': {'today': 0, 'overdue': 0, 'next_7_days': 5, },
                  'done': {'this_month': 0, 'last_month': 0, },
                  'won': {'this_month': 0, 'last_month': 0, }, 'nb_opportunities': 0, }

        return result


class trafitec_crm_trafico_resultado(models.TransientModel):
    _name = 'trafitec.crm.trafico.resultado'
    crm_trafico_id = fields.Many2one(string="", comodel_name="trafitec.crm.trafico")
    viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes')
    fecha = fields.Char(string='Fecha')
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    producto = fields.Char(string='Producto')
    asociado = fields.Char(string='Asociado')
    tarifa_a = fields.Float(string='Tarifa')
    cliente = fields.Char(string='Cliente')
    peso = fields.Float(string='Peso')
    estado = fields.Char(string='Estado')


class trafitec_crm_trafico_pedidos(models.TransientModel):
    _name = 'trafitec.crm.trafico.pedidos'
    crm_trafico_id = fields.Many2one(string="CRM", comodel_name="trafitec.crm.trafico")
    cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion')
    cotizacion_linea_id = fields.Many2one(string='Cotización línea', comodel_name='trafitec.cotizaciones.linea')
    cotizacion_linea_xid = fields.Integer(string='Cotización línea', related='cotizacion_linea_id.id')
    folio = fields.Char(string='Folio')
    fecha = fields.Char(string='Fecha')
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    producto = fields.Char(string='Producto')
    tarifa_a = fields.Float(string='Tarifa')
    cliente = fields.Char(string='Cliente')
    usuarios_asignados = fields.Char(string='Asignado a')
    peso = fields.Float(string='Peso')
    peso_viajes = fields.Float(string='Peso viajes')
    avance = fields.Float(string='Avance', default=0)
    detalles = fields.Char(string='Detalles', default='')
    semaforo_valor = fields.Char(string='Semáforo')
    lineanegocio = fields.Char(string='Línea de negocio')
    estado = fields.Char(string='Estado')

    
    def action_asociados_recomendar(self):
        obj_crm_asociados = self.env['trafitec.crm.asociados']
        return obj_crm_asociados.action_recomendar(self.cotizacion_id.id, self.cotizacion_linea_id.id)

    
    def action_asociados_recomendados(self):
        viajes_obj = self.env['trafitec.viajes']
        persona_obj = self.env['res.partner']
        obj_crm_asociados = self.env['trafitec.crm.asociados']
        # return obj.action_recomendar(self.cotizacion_linea_id.id)

        cotizacion_id = self.cotizacion_id.id
        cotizacion_municipio_origen_id = self.cotizacion_linea_id.municipio_origen_id.id
        cotizacion_municipio_destino_id = self.cotizacion_linea_id.municipio_destino_id.id

        cotizacion_estado_origen_id = self.cotizacion_linea_id.municipio_origen_id.state_sat_code.id
        cotizacion_estado_destino_id = self.cotizacion_linea_id.municipio_destino_id.state_sat_code.id

        # viajes_dat = viajes_obj.search([('origen.municipio.id', '=', cotizacion_municipio_origen_id), ('destino.municipio.id', '=', cotizacion_municipio_destino_id)])
        viajes_dat = viajes_obj.search([('origen.municipio.state_sat_code.id', '=', cotizacion_estado_origen_id),
                                        ('destino.municipio.state_sat_code.id', '=', cotizacion_estado_destino_id)])
        print("----VIAJES ENCONTRADOS--")
        print(viajes_dat)

        # Asociados recomendados de viajes.
        xids = []
        for v in viajes_dat:
            xids.append(v.asociado_id.id)

        # Asociados recomendados de usuario.
        porusuario = obj_crm_asociados.search([('linea_id', '=', self.cotizacion_linea_id.id)])
        for xu in porusuario:
            for ax in xu.asociado_id:
                xids.append(ax.id)

        # raise UserError(str(porusuario)+" Arreglo:"+str(xids))

        contexto = self._context
        filtro = []
        print("--CONTEXTO AL PRESIONAR BOTON--")
        # print(contexto)
        # print(self.ids)
        # filtro.append(('asociado', '=', True))
        filtro.append(('id', 'in', xids))

        # filtro.append(('asociado', '=', True))

        action_ctx = dict(self.env.context)
        view_id_kanban = self.env.ref('sli_trafitec.trafitec_crm_trafico_asociados_kanban').id
        view_id_form = self.env.ref('base.view_partner_form').id
        return {
            'name': 'Asociados recomendados (Folio: ' + str(self.cotizacion_id.name or '') + ' Tarifa:' + str(
                self.tarifa_a or '') + ' Origen:' + str(self.origen or '') + ' Destino:' + str(
                self.destino or '') + ')',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban,form',
            'res_model': 'res.partner',
            'views': [(view_id_kanban, 'kanban'), (view_id_form, 'form')],
            # 'form_view_ref': 'base.res_partner_kanban_view',
            # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'tree_view_ref':'',
            # 'view_id': view_id,
            # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
            'target': 'current',
            # 'res_id': self.ids[0],
            # Parametros por contexto:
            'context': {
                'cotizacion_id': cotizacion_id,
                'municipio_origen_id': cotizacion_municipio_origen_id,
                'municipio_destino_id': cotizacion_municipio_destino_id
            },
            'domain': filtro
        }


#Asociados recomendados.
"""class trafitec_crm_buscar(models.TransientModel):
    _name = 'trafitec.crm.buscar'
    _rec_name = 'id'
    buscar_nombre = fields.Char(string="Nombre")
    buscar_tiporemolque = fields.Many2one(string="Tipo remolque", comodel_name='trafitec.moviles')
    buscar_estado = fields.Char(string="Estado")
    resultado = fields.One2many(string="Resultado", comodel_name="trafitec.crm.resultado", inverse_name="buscar_id")
    info = fields.Text(string="Info", default="")
    info_ver = fields.Text(string="Info", related="info", default="")

    
    def action_buscar(self):
        return {}

    
    def action_aceptar(self):
        return {}

    
    def action_cancelar(self):
        return {}
"""
"""
class trafitec_crm_resultado(models.TransientModel):
    _name = 'trafitec.crm.resultado'
    asociado_id = fields.Many2one(string="Asociado", comodel_name="res.partner")
    buscar_id = fields.Many2one(string="Buscar", comodel_name="trafitec.crm.buscar")
"""
class trafitec_crm_trafico_asociados(models.Model):
    _name = 'trafitec.crm.asociados'
    _rec_name = 'id'

    buscar_nombre = fields.Char(string="Nombre", help='Nombre del asociado.')
    buscar_tiporemolque = fields.Many2one(string="Tipo remolque", comodel_name='trafitec.moviles', help='Tipo de remolque que tiene el asociado.')
    buscar_estado = fields.Many2one(string="Estado", comodel_name='res.country.state', help='Estado del país donde radica el asociado.')

    asociado_id = fields.Many2many(string='Asociados', comodel_name='res.partner', help='Asociados.')
    asociado_nombre = fields.Char(string='Asociado', related='asociado_id.name', help='Asociado.')
    cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion', help='Cotización.')
    linea_id = fields.Many2one(string='Origen destino', comodel_name='trafitec.cotizaciones.linea', help='Cotización.')
    tipo_recomendacion = fields.Selection(string='Tipo', selection=[('porviajes', 'Por viajes'), ('porusuario', 'Por usuario')], default='porusuario')

    @api.model
    def get_empty_list_help(self, help):
        help = "No se encontraron asociados recomendados por usuarios."
        return help

    
    def action_quitar_asociados(self):
        #Limpia la lista.
        self.asociado_id = None

    
    def action_buscar_asociados(self):
        self.asociado_id = None
        lista = []
        filtro = []

        #Solo asociados.
        filtro.append(('asociado', '=', True))
        if self.buscar_nombre:
            filtro.append(('name', 'ilike', '%'+str(self.buscar_nombre or '')+'%'))

        if self.buscar_tiporemolque:
            filtro.append(('trafitec_unidades_id.movil', '=', self.buscar_tiporemolque.id))

        if self.buscar_estado:
            filtro.append(('state_id', '=', self.buscar_estado.id))

        asociados = self.env['res.partner'].search(filtro, limit=100)
        #_logger.info(str(asociados))
        for a in asociados:
            lista.append(a.id)
        self.asociado_id = None
        self.asociado_id = lista
        #return {}

    def action_recomendar(self, cotizacion_id, linea_id):
        view_id = self.env.ref('sli_trafitec.trafitec_crm_recomendar_form').id
        return {'name': 'Recomendar asociados',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.crm.asociados',
                 'views': [(view_id, 'form')],
                # 'form_view_ref': 'base.res_partner_kanban_view',
                # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
                # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
                # 'tree_view_ref':'',
                'view_id': view_id,  # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
                'target': 'current',  #current, new, main 'res_id': self.ids[0],
                'context': {
                    'default_cotizacion_id': cotizacion_id,
                    'default_linea_id': linea_id
                }
        }

    
    def action_crear(self, vals):
        return super(trafitec_crm_trafico_asociados, self).create(vals)

    
    def action_cerrar(self):
        return {}

class trafitec_crm_trafico_registro(models.Model):
    _name = 'trafitec.crm.trafico.registro'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'
    _rec_name = 'id'
    asociado_id = fields.Many2one(string='Asociado', comodel_name='res.partner', track_visibility='onchange')
    asociado_id_txt = fields.Char(string='Asociado', related='asociado_id.name', readonly=True)

    detalles = fields.Char(string='Detalles', default='', required=True, track_visibility='onchange')
    tipo = fields.Selection(string='Tipo',
                            selection=[('llamada_telefonica', 'Llamada telefónica'), ('email', 'Correo electrónico'),
                                       ('mensajero_instataneo', 'Mensajero instantaneo')], default='llamada_telefonica',
                            required=True, track_visibility='onchange')
    generar_evento_st = fields.Boolean(string='Registrar evento en calendario', default=False)
    generar_evento_dias = fields.Integer(string='Dias para nuevo evento', default=3)
    generar_evento_fechahora = fields.Datetime(string='Fecha para nuevo evento')

    
    @api.depends('viajes_id')
    def _compute_numero_viajes(self):
        self.viajes_n = len(self.viajes_id)

    seg_modificar = fields.Boolean(string='Permitir modificar', default=True, track_visibility='onchange')
    cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion',
                                    track_visibility='onchange')
    cotizacion_id_txt = fields.Char(string='Cotización', related='cotizacion_id.name', readonly=True)
    viajes_id = fields.One2many(string='Viajes', comodel_name='trafitec.crm.trafico.registro.viajes',
                                inverse_name='registro_id')
    viajes_n = fields.Integer(string='Número de viajes', compute=_compute_numero_viajes, default=0, store=True)
    motivo_rechazo_id = fields.Many2one(string='Motivo de rechazo', comodel_name='trafitec.clasificacionesg',
                                        track_visibility='onchange')
    tarifa = fields.Float(string='Tarifa', default=0)
    state = fields.Selection(string='Estado',
                             selection=[('nuevo', 'Nuevo'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')],
                             default='nuevo', track_visibility='onchange', required=True)

    @api.model
    def default_get(self, fields):
        res = super(trafitec_crm_trafico_registro, self).default_get(fields)

        print("--CONTEXT EN DEFAULT_GET")
        print(self._context)
        print("--RES")
        print(res)
        print("--FIELDS")
        print(fields)

        if 'cotizacion_id' in self._context and 'active_id' in self._context:
            cotizacion_id = self._context.get('cotizacion_id', None)
            asociado_id = self._context.get('active_id', None)
            cotizacion_dat = self.env['trafitec.cotizacion'].browse([cotizacion_id])
            persona_dat = self.env['res.partner'].browse([asociado_id])
            res.update(
                {
                    'cotizacion_id': cotizacion_dat.id,
                    'cotizacion_id_txt': cotizacion_dat.name,
                    'asociado_id': persona_dat.id,
                    'asociado_id_txt': persona_dat.name
                }
            )
        print("--RES2")
        print(res)
        return res

    @api.onchange('state')
    def _onchange_state(self):
        if self.state != 'rechazado':
            self.motivo_rechazo_id = False

    # if self.state != 'aceptado':
    #	self.viajes_id = None

    
    def action_aceptado(self):
        self.state = 'aceptado'

    
    def action_rechazado(self):
        self.state = 'rechazado'

    def valida(self, vals=None, tipo=1):  # 1=Crear, 2=Modificar, 3=Borrar.
        if len(self) <= 0:
            print("***NUEVO")
        else:
            print("***EXISTENTE")

        dias = 0
        print("-----LOS VALS-----" + str(tipo))
        print(vals)
        print("-----SELF-----")
        print(self)

        if vals:
            if 'generar_evento_fechahora' in vals and 'generar_evento_st' in vals:

                if vals['generar_evento_st']:
                    fechahora = vals['generar_evento_fechahora']
                    if not fechahora:
                        raise UserError(_('Debe especificar la fecha y hora para el nuevo evento.'))

        """
            if 'state' in vals:
                if vals['state'] == 'aceptado':
                    if not 'viajes_id' in vals or len(vals.get('viajes_id', [])) <= 0:
                        raise UserError(_('Debe especificar los viajes.'))
        """

        state = ''
        viajes_id = []
        motivo_rechazo_id = None
        tarifa = 0.00
        if tipo == 1:  # Crear.
            state = vals['state']
            # viajes_id = vals['viajes_id']
            motivo_rechazo_id = vals['motivo_rechazo_id']
            tarifa = vals['tarifa']
        elif tipo == 2:  # Modificar.
            # registro_dat = self.env['trafitec.crm.trafico.registro'].browse([self.id])
            if 'state' in vals:
                state = vals['state']
            else:
                state = self.state

            """
            if 'viajes_id' in vals:
                viajes_id = vals['viajes_id']
            else:
                viajes_id = self.viajes_id
            """

            if 'motivo_rechazo_id' in vals:
                motivo_rechazo_id = vals['motivo_rechazo_id']
            else:
                motivo_rechazo_id = self.motivo_rechazo_id

            if 'tarifa' in vals:
                tarifa = vals['tarifa']
            else:
                tarifa = self.tarifa

        if state == 'aceptado':
            """
            if len(viajes_id) <= 0:
                raise UserError(_('Debe especificar al menos un viaje.'))
            """

            if tarifa <= 0:
                raise UserError(_('Debe especificar la tarifa'))

        if state == 'rechazado':
            if not motivo_rechazo_id:
                raise UserError(_('Debe especificar el motivo de rechazo'))

            """
            if len(viajes_id) > 0:
                raise UserError(_('Debe quitar los viajes relacionados.'))
            """

    @api.model
    def create(self, vals):
        self.valida(vals, 1)

        persona_obj = self.env['res.partner']
        persona_dat = None

        if 'active_id' in self._context:
            vals['asociado_id'] = self._context['active_id']

        if 'cotizacion_id' in self._context:
            vals['cotizacion_id'] = self._context['cotizacion_id']

        # Lo marca como generado.
        vals.update({'seg_modificar': False})

        nuevo = super(trafitec_crm_trafico_registro, self).create(vals)
        print("---CONTEXTO AL ACTUALIZAR---")
        print(self._context)
        if 'active_id' in self._context:
            persona_dat = persona_obj.search([('id', '=', self._context['active_id'])])
            persona_dat.write({
                'crm_trafico_ultimocontacto_fechahora': datetime.datetime.today(),
                'crm_trafico_ultimocontacto_usuario_id': self._uid
            })
        # self.asociado_id.crm_trafico_ultimocontacto_fechahora = datetime.datetime.today()  # +timedelta(days=-3)
        # self.asociado_id.crm_trafico_ultimocontacto_usuario_id = self._uid

        if nuevo.generar_evento_st:
            tipo_txt = 'Contactar a: '

            print("---Contactar a---")
            print(nuevo.asociado_id)

            if persona_dat:
                tipo_txt += (persona_dat.name or persona_dat.display_name or '')

            calendario_obj = self.env['calendar.event']
            nuevoevento = {
                'name': tipo_txt,
                'user_id': self.env.user.id,
                'description': nuevo.detalles,
                'start': str(nuevo.generar_evento_fechahora),
                'stop': str(nuevo.generar_evento_fechahora)  # nuevo.generar_evento_fechahora + timedelta(hours=1)
            }
            calendario_obj.create(nuevoevento)

        self._proceso_rechazo(vals, nuevo)

        return nuevo

    
    def write(self, vals):
        self.valida(vals, 2)

        # vals.update({'seg_modificar':False})
        modificado = super(trafitec_crm_trafico_registro, self).write(vals)

        self._proceso_rechazo(vals, modificado)
        return modificado

    def _proceso_rechazo(self, vals, obj=None):
        state = ''
        asociado_id = None

        if 'state' in vals:
            state = vals.get('state', '')

            if 'asociado_id' in vals:
                asociado_id = vals.get('asociado_id', None)
            else:
                asociado_id = self.asociado_id.id

            if state == 'rechazado' and asociado_id and obj:
                persona_dat = self.env['res.partner'].browse([asociado_id])
                persona_dat.write({'crm_trafico_ultimo_rechazo_id': obj.id})
        return


class trafitec_crm_trafico_registro_viajes(models.Model):
    _name = 'trafitec.crm.trafico.registro.viajes'
    registro_id = fields.Many2one(string='Registro', comodel_name='trafitec.crm.trafico.registro')
    viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes', required=True)

    @api.model
    def create(self, vals):
        nuevo = super(trafitec_crm_trafico_registro_viajes, self).create(vals)
        nuevo.viaje_id.crm_trafico_registro_id = nuevo.id
        return nuevo

    
    def unlink(self):
        self.viaje_id.crm_trafico_registro_id = False
        borrado = super(trafitec_crm_trafico_registro_viajes, self).unlink()
        # self.viaje_id.write({'crm_trafico_registro_id', False})
        return borrado


class trafitec_crm_trafico_tablero(models.Model):
    _name = "trafitec.crm.trafico.tablero"

    # def init(self):
    # print("---SELF INIT---")
    # print(self)

    # print("---CONTEXT INIT---")
    # print(self._context)

    # try:
    # tablero_obj = self.env['trafitec.crm.trafico.tablero']
    # tablero_dat = self.env['trafitec.crm.trafico.tablero'].search([])
    # if len(tablero_dat) <= 0:
    #	tablero_obj.create({'name': 'CRM TRAFICO 3', 'color': 1})
    # except:
    #	print("**Error al inicializar el registro de CRM Tráfico.")

    
    def _compute_cotizaciones_disponibles_n(self):
        n = self.env['trafitec.cotizacion'].search([('state', '=', 'Disponible')])
        self.cotizaciones_disponibles_n = len(n)

    
    def _compute_misviajeshoy_n(self):
        n = self.env['trafitec.viajes'].search_count([('state', '=', 'Nueva'), ('create_uid', '=', self.env.user.id),
                                                      ('create_date', '>=', str(datetime.datetime.today().date()))])
        self.misviajeshoy_n = n

    
    def _compute_misviajes_n(self):
        n = self.env['trafitec.viajes'].search_count([('state', '=', 'Nueva'), ('create_uid', '=', self.env.user.id), (
            'create_date', '>=', (datetime.date.today() + timedelta(days=-7)).strftime("%Y-%m-%d"))])
        self.misviajes_n = n

    
    def _compute_misviajesc_n(self):
        n = self.env['trafitec.viajes'].search_count([('state', '!=', 'Nueva'), ('create_uid', '=', self.env.user.id)])
        self.misviajesc_n = n

    name = fields.Char(string="Nombre")
    color = fields.Integer(string='Color')
    cotizaciones_disponibles_n = fields.Integer(string="Cotizaciones disponibles",
                                                compute=_compute_cotizaciones_disponibles_n, store=False)
    misviajes_n = fields.Integer(string="Mis viajes recientes", compute=_compute_misviajes_n, store=False)
    misviajeshoy_n = fields.Integer(string="Mis viajes hoy", compute=_compute_misviajeshoy_n, store=False)
    misviajesc_n = fields.Integer(string="Mis viajes cancelados", compute=_compute_misviajesc_n, store=False)

    def action_abrir_crm_cotizaciones(self):
        # view_id = self.env.ref('sli_trafitec.trafitec_crm_trafico_form').id
        return {
            'name': 'CRM Tráfico',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.crm.trafico',
            # 'views': [(view_id, 'tree')],
            # 'form_view_ref': 'base.res_partner_kanban_view',
            # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'tree_view_ref':'',
            # 'view_id': view_id,
            # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
            'target': 'current',
            'multi': True,
            # 'res_id': self.ids[0],
            'context': self._context,
            # 'domain': []
        }

    def action_abrir_crm_viajes(self):
        return {}

    def action_abrir_cotizaciones(self):
        # view_id = self.env.ref('sli_trafitec.view_cotizacion_tree').id
        return {
            'name': 'Mis cotizaciones (' + (self.env.user.name or '') + ')',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.cotizacion',
            # 'views': [(view_id, 'tree')],
            # 'form_view_ref': 'base.res_partner_kanban_view',
            # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'tree_view_ref':'',
            # 'view_id': view_id,
            # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'target': 'new',
            # 'res_id': self.ids[0],
            'context': {},
            'domain': [('create_uid', '=', self.env.user.id)]
        }

    def action_abrir_viajes(self):
        # view_id = self.env.ref('sli_trafitec.view_viajes_tree').id
        return {
            'name': 'Mis viajes (' + (self.env.user.name or '') + ')',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.viajes',
            # 'views': [(view_id, 'tree')],
            # 'form_view_ref': 'base.res_partner_kanban_view',
            # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'tree_view_ref':'',
            # 'view_id': view_id,
            # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
            # 'target': 'new',
            # 'res_id': self.ids[0],
            'context': {},
            'domain': [('create_uid', '=', self.env.user.id)]
        }
