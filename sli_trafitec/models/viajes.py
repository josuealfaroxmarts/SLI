## -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
import random
import sys

_logger = logging.getLogger(__name__)


class trafitec_viajes(models.Model):
    _name = 'trafitec.viajes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    """
    
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        #if view_type == 'form':
        #    raise UserError("Fields get: "+str(fields))
        res = super(trafitec_viajes, self).fields_get(self, view_id=None, view_type=False, toolbar=False, submenu=False)
        return res
    """

    @api.model
    def get_empty_list_help(self, help):
        help = "No se encontraron viajes.."
        return help

    
    
    def export_data(self, fields_to_export, raw_data=False):
        #_logger.info(str(dir(models.Model)))
        """ Override to convert virtual ids to ids """
        
        """
        if 'tarifa_cliente' in fields_to_export:
            raise UserError('No tiene permisos para exportar Tarifa cliente.')

        if 'asociado_id/name' in fields_to_export:
            raise UserError('No tiene permisos para exportar el asociado.')
        """
        if ('tarifa_cliente' in fields_to_export) or ('flete_cliente' in fields_to_export):
            if not self.env.user.has_group('sli_trafitec.sli_trafitec_ver_tc'):
                grupo = self.env.ref('sli_trafitec.sli_trafitec_ver_tc')
                raise ValidationError('Solo usuarios en el grupo (%s) pueden exportar la tarifa cliente/flete cliente.' % grupo.name)
        
        #datos = []
        nuevo = super(trafitec_viajes, self).export_data(fields_to_export, raw_data)
        
        
        #for d in nuevo:
        #    datos.append(d)
        
        #raise UserError("Datos: "+str(nuevo)+" Campos:"+str(fields_to_export)+" Tipo: "+str(type(fields_to_export))+" ")
        records = [] #self.browse(set(get_real_ids(self.ids)))
        return nuevo

    """
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        #raise UserError("Fields get")
        res = super(trafitec_viajes, self).fields_get(cr, uid, view_id=None, view_type='form', context=None, toolbar=False)
        return res
    """
    
    """
    def export_data(self, cr, uid, ids, fields, context=None):
        return super(trafitec_viajes, self).export_data(cr, uid, ids, fields, context=None)
    """
    cliente_bloqueado = fields.Boolean(string='Cliente bloqueado', related='cliente_id.bloqueado_cliente_bloqueado', store=True, default=False, help='Indica si el cliente esta bloqueado.')
    #cliente_bloqueado_st = fields.Boolean(string='Cliente bloqueado', default=False, related="cliente_id.bloqueado_cliente_bloqueado", store=True, help='Indica si el cliente esta bloqueado.')

        
    
    #Origenes y destino tab.
    active = fields.Boolean(default=True)
    # cotizacion_id=fields.Many2one(comodel_name='trafitec.cotizaciones',string='Cotización',required=True)
    linea_id = fields.Many2one('trafitec.cotizaciones.linea', string='Número de cotización',
                                required=True, change_default=True, index=True, track_visibility='always')
    cotizacion_asegurado = fields.Boolean(string='Esta asegurado',related='linea_id.cotizacion_id.seguro_mercancia', readonly=True, store=True)
    vendedor_id = fields.Many2one(string='Vendedor',related='linea_id.cotizacion_id.create_uid', readonly=True, store=True)

    moneda = fields.Many2one("res.currency", related='linea_id.cotizacion_id.currency_id', string="Moneda", store=True)
    cliente_id = fields.Many2one('res.partner', string='Cliente', required=True,
                                domain="[('company_type','in',['company','person']),('customer','=',True)]")
    referencia_cliente = fields.Char(string="Referencia Viaje Cliente")
    referencia_fletex = fields.Char(string="Referencia Viaje Cliente")
    referencia_asociado = fields.Char(string="Referencia Viaje Asociado")
    origen = fields.Many2one(related='linea_id.cotizacion_id.origen_id', string='Ubicación origen', store=True, required=True, readonly=True)
    destino = fields.Many2one(related='linea_id.cotizacion_id.destino_id', string='Ubicación destino', store=True, required=True, readonly=True)
    facturar = fields.Boolean(string='Facturar', readonly=True, store=True)
    psf = fields.Boolean(string='PSF', track_visibility='onchange')
    csf = fields.Boolean(string='CSF', track_visibility='onchange')
    tarifa_asociado = fields.Float(string='Tarifa asociado', default=0, track_visibility='onchange', related='linea_id.tarifa_asociado', required=True)
    tarifa_cliente = fields.Float(string='Tarifa cliente', default=0,required=True)
    tarifa_cliente_colaborador = fields.Float(string='Tarifa cliente colaborador', default=0, required=False)
    product = fields.Many2one('product.product', string='Producto',
                                related='linea_id.cotizacion_id.product', readonly=True, store=True)
    costo_producto = fields.Float(string='Costo del producto', track_visibility='onchange')

    lineanegocio = fields.Many2one(comodel_name='trafitec.lineanegocio', string='Linea de negocios', store=True)
    tipo_lineanegocio = fields.Char('Tipo de linea de negocio', related='lineanegocio.name', store=True)

    comision_linea = fields.Float(string='Porcentaje linea negocio', related='lineanegocio.porcentaje', readonly=True,
                                    store=True)
    company_id = fields.Many2one('res.company',
                                    default=lambda self: self.env['res.company']._company_default_get('trafitec.viajes'))
    state = fields.Selection([('Nueva', 'Nueva'), ('Siniestrado', 'Siniestrado'), ('Cancelado', 'Cancelado')],
                                string='Estado',
                                default='Nueva', track_visibility='onchange')
    documentacion_completa = fields.Boolean(string='Documentanción completa')
    fecha_viaje = fields.Date(string='Fecha del viaje', readonly=False, index=True, copy=False,
                                default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='Usuario que genero viaje', index=True, track_visibility='onchange',
                                default=lambda self: self.env.user)
    motivo_siniestrado = fields.Text(string='Motivo siniestrado', track_visibility='onchange')
    motivo_cancelacion = fields.Text(string='Motivo cancelacion', track_visibility='onchange')
    fecha_cambio_estado = fields.Datetime(string='Fecha de cambio')

    en_contrarecibo = fields.Boolean(string="Viaje en contra recibo", default=False)
    contrarecibo_id = fields.Many2one(string="Contra recibo",comodel_name='trafitec.contrarecibo')
    contrarecibo_fecha = fields.Date(string="Fecha contra recibo", related='contrarecibo_id.fecha', store=True)

    x_folio_trafitecw = fields.Char(string='Folio Trafitec Windows', help="Folio de la orden de carga en Trafitec para windows.")
    sucursal_id = fields.Many2one('trafitec.sucursal', string='Sucursal', store=True)
    cargo_id = fields.One2many('trafitec.viaje.cargos', 'line_cargo_id')
    cargo_total = fields.Float(string='Total cargos', compute='compute_cargo_total', store=True)

    en_factura = fields.Boolean(string="Viaje con factura cliente", default=False)
    factura_cliente_id = fields.Many2one(string='Factura cliente',comodel_name='account.move')  # Mike, indica en que factura esta el viaje
    factura_cliente_folio = fields.Char(string='Folio de factura cliente', related='factura_cliente_id.name',store=True)
    factura_cliente_fecha = fields.Date(string='Fecha de factura cliente', related='factura_cliente_id.date',store=True)

    en_cp = fields.Boolean(string="Viaje con carta porte", default=False, help='Indica si el viaje esta relacionado con una carta porte.')
    factura_proveedor_id = fields.Many2one(string='Factura proveedor', comodel_name='account.move')  # Mike, indica en que factura proveedor esta el viaje
    factura_proveedor_folio = fields.Char(string='Folio de factura proveedor', related='factura_proveedor_id.name', store=True)
    factura_proveedor_fecha = fields.Date(string='Fecha de factura proveedor', related='factura_proveedor_id.date', store=True)

    asignadoa_id = fields.Many2one(string='Asignado a',comodel_name='res.users', track_visibility='onchange')
    
    
    estado_viaje = fields.Selection(string='Estado del viaje', selection = [('noespecificado','(No especificado)'),('enespera','(En espera)'),('enproceso','En proceso'),('finalizado','Finalizado'),('cancelador','Cancelado'), ('cerrado','Cerrado'),('siniestrado','Siniestrado')],default='enespera', track_visibility='onchange')
    proyecto_referenciado = fields.Char(string='Proyecto referenciado', readonly=True, related='linea_id.cotizacion_id.nombre')
    calificaiones = fields.One2many(string='Calificaciones', inverse_name='viaje_id', comodel_name = 'trafitec.clasificacionesgxviaje', track_visibility='onchange')

    crm_trafico_registro_id = fields.Many2one(string='Registro CRM Tráfico', comodel_name='trafitec.crm.trafico.registro')

    cantidad = fields.Char(string='cantidad', default="0")
    cliente_etiquetas = fields.Many2many(string='Etiqueta del cliente', comodel_name='res.partner.category', related='cliente_id.category_id')
    name = fields.Char(string="Folio", required=True, copy=False, readonly=True,
                    index=True, default=lambda self: _('New'))

    router = fields.Char(
        string='Ruta (Google Maps)',
    )

    @api.onchange('referencia_asociado')
    def gelocalization(self):

        domain = [('shipment_id_fletex', '=', self.referencia_asociado)]

        for geo in self.env['trafitec.routers'].search(domain):
            self.router = geo.google_maps


    @api.onchange('seguro_total', 'seguro_entarifa')
    def onchange_seguro(self):
        original = {}
        originales = []
        final = {}
        finales = []
        total = 0
        existe = False
        
        #Tuplas finales.
        tfinal = {}
        tfinales = []

        # Obtener de configuracion el producto que se usara para el seguro de carga.
        cfg_obj = self.env['trafitec.parametros']
        cfg_dat = cfg_obj.search([('company_id', '=', self.env.user.company_id.id)], limit=1)

        #seguro_cargo_adicional_id
        #Originales
        for l in self.cargo_id:
            original = {
                'id': l.id,
                'line_cargo_id': l.line_cargo_id,
                'sistema': l.sistema,
                'validar_en_cr': l.validar_en_cr,
                'name': l.name,
                'valor': l.valor
            }
            originales.append(original)

        _logger.info("----ORIGINALES----"+str(original))

        #Finales
        valor = 0
        xid = -1
        for o in originales:
            xid = o.get('id')
            valor = o.get('valor', 0)
            
            #Auita los que no tengan valor.
            if valor <= 0:
                continue
            
            _logger.info("-----------------------------------------------------------------------------------------------")
            _logger.info("------------------------TIPO:: "+str(type(xid))+" ::-----------------------------------")
            _logger.info("------------------------XID:: "+str(xid)+" ::-----------------------------------")
            _logger.info("-----------------------------------------------------------------------------------------------")
            _logger.info("------------------------TIPO models.NewId:: "+str(type(models.NewId))+" ::-----------------------------------")
            _logger.info("------------------------models.NewId:: "+str(models.NewId)+" ::-----------------------------------")
            
            if o.get('name').id == cfg_dat.seguro_cargo_adicional_id.id:
                if self.seguro_entarifa:
                    continue
                
                if not isinstance(xid, models.NewId):
                    valor = self.seguro_total
                    existe = True
                else:
                    continue
            
            final = {'accion': 'actualizar', 'id': o.get('id'), 'registro': {
                'name': o.get('name'), #Tipo de cargo adicional, obtener de configuracion general.
                'valor': valor,  #o.get('valor'),
                'line_cargo_id': o.get('line_cargo_id'), #El viaje actual.
                'sistema': o.get('sistema'),
                'validar_en_cr': o.get('validar_en_cr')
            }
            }
            #finales += [(1, o.get('id'), final)]
            finales.append(final)
            
        if not existe and not self.seguro_entarifa and self.seguro_total > 0:
            producto_seguro = self.env['trafitec.tipocargosadicionales'].search([('name', '=', 'Seguro')])
            seguro = {'accion': 'crear', 'id': -1, 'registro': {
                'name': producto_seguro.id, #Tipo de cargo adicional, obtener de configuracion general.
                'valor': self.seguro_total,  #o.get('valor'),
                'line_cargo_id': self.id, #El viaje actual.
                'sistema': True,
                'validar_en_cr': False,
                'tipo': 'pagar_cr_cobrar_f'
                }
            }
            #finales += [(0, 0, seguro)]
            finales.append(seguro)
        
        
        _logger.info("----FINALES----" + str(finales))

        #Tuplas finales.
        for f in finales:
            if f.get('accion') == 'crear':
                tfinal = (0, 0, f.get('registro'))
            if f.get('accion') == 'actualizar':
                tfinal = (1, f.get('id'), f.get('registro'))
            
            tfinales += [tfinal]


        _logger.info("----TFINALES----" + str(tfinales))
        #self.cargo_id = tfinales
        self.update({'cargo_id': tfinales})
    
    #Poliza de seguro
    
    @api.depends('seguro_pcliente', 'costo_producto', 'peso_origen_total', 'seguro_id')
    def copute_seguro_total(self):
        total = 0

        #Calculo del seguro.
        total = (self.peso_origen_total * self.costo_producto * self.seguro_pcliente)
        self.seguro_total = total

    seguro_id = fields.Many2one(string='Poliza de seguro', comodel_name='trafitec.polizas', related='linea_id.cotizacion_id.polizas_seguro') #Poliza relacionada.
    seguro = fields.Boolean(string="Seguro", related='linea_id.cotizacion_id.seguro_mercancia')
    seguro_pcliente = fields.Float(string='Factor del seguro', default=0, help='Factor del seguro.', digits=(16, 3), related='linea_id.cotizacion_id.factor_seguro') #Porcentaje para el cliente.
    seguro_total = fields.Float(string='Total del seguro', compute=copute_seguro_total, default=0, store=True)
    seguro_entarifa = fields.Boolean(string='Seguro incluido en tarifa', default=False, help='Indica si el seguro esta incluido en la tarifa.', related='linea_id.cotizacion_id.seguro_entarifa')

    descuento_combustible_id = fields.Many2one(string='Vale de combustible', comodel_name='trafitec.descuentos', help='Descuento de vale de combustible.')

    
    def action_descuento_combustible(self):
        self.ensure_one()

        viaje = self
        error = False
        errores = ""

        #Validaciones.
        if viaje.descuento_combustible_id:
            error = True
            errores +="El viaje ya tiene relacionado un vale de combustible.\n"

        if viaje.state != 'Nueva':
            error = True
            errores+="El viaje debe estar activo.\n"

        if viaje.en_contrarecibo:
            error = True
            errores+="El viaje ya esta en contra recibo.\n"

        if viaje.en_factura:
            error = True
            errores+="El viaje ya esta en factura.\n"


        if not viaje.asociado_id.combustible_convenio_st:
            error = True
            errores+='El asociado {} no tiene convenio de combustible.\n'.format(viaje.asociado_id.name or '')
        
        
        if error:
            raise UserError(errores)

        #Objetos.
        descuentos_obj = self.env["trafitec.descuentos"]
        cfg_obj = self.env['trafitec.parametros']
        cfg = cfg_obj.search([('company_id', '=', self.env.user.company_id.id)], limit=1)

        pfactor = (cfg.descuento_combustible_pfactor or 0) / 100
        pcomision = (cfg.descuento_combustible_pcomision or 0) / 100

        litros = 0
        costoporlt = (cfg.descuento_combustible_externo_id.list_price or 0)

        flete = 0
        if viaje.flete_asociado > 0:
            flete = viaje.flete_asociado
        else:
            flete = (viaje.peso_autorizado / 1000) * viaje.tarifa_asociado

        total = flete * pfactor
        comision = total * pcomision
        totalvale = total + comision

        if costoporlt != 0:
            litros = total / costoporlt

        proveedor_id = (cfg.descuento_combustible_proveedor_id.id or False)
        concepto_id = (cfg.descuento_concepto_id.id or False)

        if not proveedor_id or not concepto_id:
            return

        #_logger.info(valores)

        if totalvale <= 0:
            raise UserError('El total del desucuento debe ser mayor a cero.')
            
        valores = {
            'proveedor': proveedor_id,
            'monto': totalvale,
            'abono_total': 0,
            'operador_id': viaje.operador_id.id,
            'cobro_fijo': False,
            'fecha': False,
            'state': 'borrador',
            'asociado_id': viaje.asociado_id.id,
            'saldo': totalvale,
            'viaje_id': viaje.id,
            'monto_cobro': totalvale,
            'concepto': concepto_id,
            'comentarios': 'Generado desde el viaje {0} con flete de {3:,.2f} para {1:,.2f} litros de combustible con un costo por litro de {2:,.2f}.'.format(viaje.name, litros, costoporlt,flete),

            'es_combustible': True,
            'folio_nota': '',
            'es_combustible_litros': litros,
            'es_combustible_costoxlt': costoporlt,
            'es_combustible_total': total,
            'es_combustible_pcomision': pcomision*100,
            'es_combustible_comision': comision,
            'es_combustible_totalcomision': totalvale
        }
        nuevo = descuentos_obj.create(valores)
        viaje.write({'descuento_combustible_id': nuevo.id})

    
    @api.depends('cargo_id')
    def compute_cargo_total(self):
        total = 0
        for c in self.cargo_id:
            total += c.valor
            
        self.cargo_total = total
    
    
    
    def action_nueva(self):
        self.ensure_one()
        self.state = 'Nueva'
        

    
    def action_scan(self):
        self.ensure_one()
        obj = self.env['trafitec.viajes.scan'].search([])
        print("**Scan : " + str(obj))

        if len(obj) == 'started':
            if obj.viaje_id and self.id:
                if obj.viaje_id.id != self.id and obj.st == 'started':
                    raise UserError(_('Alerta..\nEl proceso de Scan esta activo en otro viaje: '+str(obj.viaje_id.name)))

            if obj.st == 'started':
                obj.st = 'not_started'
                return self.Mensaje("Scan terminado.")
            else:
                obj.st = 'started'
                obj.viaje_id = self.id
                return self.Mensaje("Scan iniciado.")
        else:
            if self.id:
                nuevo={'viaje_id': self.id, 'st': 'started'}
                print("**Scan nuevo:"+str(nuevo))
                obj.create(nuevo)
                return self.Mensaje("Scan iniciado.")
        
    def Mensaje(self, mensaje):
        return {
            'name': 'Alerta..',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': mensaje}
        }

    def viajes_conteo(self):
        return 23

    @api.model
    def default_get(self, fields):
        rec = super(trafitec_viajes, self).default_get(fields)
        #rec.update({'costo_producto': 3.14})
        print("****DEFAULT GET VIAJES*****")
        print(rec)
        return rec
    
    #Regresa el total de viajes.
    def total_viajes(self, creando=False):
        total = 0.00 #Total de la cotizacion.
        totalesteviaje = 0.00 #Total de este viaje.
    
        #Obtener el viaje actual.
        #if creando:
        #    if self.peso_origen_total <= 0:
        #        totalesteviaje = self.tipo_remolque.capacidad
        #        print("===VIAJE SIN PESO:" + str(self.tipo_remolque.capacidad))
        #    else:
        #        totalesteviaje = self.peso_origen_total / 1000.00
        #        print("===VIAJE CON PESO:" + str(self.peso_origen_total))
        
        
        #Obtener el resto de viajes.
        viajes=self.env['trafitec.viajes'].search([('linea_id', '=', self.id),('state','=','Nueva')])
        for v in viajes:
            if v.peso_origen_total <= 0:
                #total = total + v.tipo_remolque.capacidad
                total = total + v.peso_autorizado
            else:
                total = total + v.peso_origen_total / 1000.00
            
        total = total + totalesteviaje
        return total
    
    
    def unlink(self):
        #self.Valida(3)
        #print(dir(self))
        raise UserError(_('Alerta..\nNo esta permitido borrar viajes.'))
        
        for reg in self:
            if reg.en_contrarecibo == True:
                raise UserError(
                    _('Alerta..\nNo se puede eliminar un viaje ({}) que tenga contra recibo.'.format(reg.name)))
            if reg.en_factura == True:
                raise UserError(_(
                    'Aviso !\nNo se puede eliminar un viaje ({}) que tenga factura.'.format(reg.name)))
            
            obj_comison = self.env['trafitec.cargos'].search([('viaje_id', '=', reg.id)])
            for cargo in obj_comison:
                if cargo.tipo_cargo == 'comision':
                    cargo.write({'viaje_id': False})
                cargo.unlink()
        return super(trafitec_viajes, self).unlink()

    
    @api.constrains('cliente_id',
                    'lineanegocio',
                    'asociado_id',
                    'operador_id',
                    'placas_id',
                    'peso_origen_remolque_1',
                    'peso_origen_remolque_2',
                    'peso_destino_remolque_1',
                    'peso_destino_remolque_2',
                    'peso_convenido_remolque_1',
                    'peso_convenido_remolque_2',
                    'peso_origen_total',
                    'peso_destino_total',
                    'peso_autorizado',
                    'seguro_id',
                    'costo_producto',
                    'seguro_pcliente',
                    'seguro_total',
                    'seguro_entarifa'
                    'cargo_id',
                    'flete_cliente')
    
    def _valida(self):
        
        if not self.cliente_id:
            raise UserError(_('Alerta !\n--Debe especificar el cliente.'))

        if not self.lineanegocio:
            raise UserError(_('Alerta !\nDebe especificar la línea de negocio.'))

        if not self.asociado_id:
            raise UserError(_('Alerta !\nDebe especificar el asociado.'))

        if not self.operador_id:
            raise UserError(_('Alerta !\nDebe especificar el operador.'))

        if not self.placas_id:
            raise UserError(_('Alerta !\nDebe especificar el vehículo.'))

        if not self.asociado_id:
            raise UserError(_('Alerta !\nDebe especificar el asociado.'))

        if not self.operador_id:
            raise UserError(_('Alerta !\nDebe especificar el operador.'))

        #Validacion del seguro.
        
        #Si esta asegurado
        if self.flete_cliente > 0:
            if self.seguro_id:
                if not self.seguro_entarifa:
                    if self.costo_producto <= 0:
                        raise UserError(_('Alerta..\nEste viaje esta asegurado, debe especificar el costo del producto por kg.'))
                    
                    if self.seguro_pcliente <= 0:
                        raise UserError(_('Alerta..\nEste viaje esta asegurado, debe especificar el porcentaje de seguro.'))
        
                    if self.seguro_total <= 0:
                        raise UserError(_('Alerta..\nEste viaje esta asegurado, el total del seguro debe ser mayor a cero.'))

            
        total_viajes = self.total_viajes()
        total_subpedido = self.cantidad

        print("================Total viajes:: " + str(total_viajes) + " Total subpedido:: " + str(total_subpedido))
        if total_viajes > 0 and total_subpedido > 0 and total_viajes > total_subpedido:
            raise UserError(_(
                'Alerta..\nCon el viaje actual se excede el peso de lo especificado en la cotización ({}/{}).'.format(
                    total_viajes, total_subpedido)))
        
        #Cargos adicionales.
        """
        for c in self.cargo_id:
            if c.valor <= 0:
                raise UserError(_('El valor de los cargos adicionales deben ser mayor a cero.'))
            
            if c.valor > 5000:
                raise UserError(_('El valor de los cargos adicionales deben ser menor a 10,000.00'))
        """

        # Pesos
        if self.lineanegocio.id == 1:  # Si es granel.
            if self.peso_origen_remolque_1 > 0 and (self.peso_origen_remolque_1 > 150000):
                raise UserError(_('Alerta !\nEl peso origen del remolque 1 debe estar entre 1 y 150,000.'))

            if self.peso_origen_remolque_2 > 0 and (self.peso_origen_remolque_2 > 150000):
                raise UserError(_('Alerta !\nEl peso origen del remolque 2 debe estar entre 1 y 150,000.'))

            if self.peso_destino_remolque_1 > 0 and (self.peso_destino_remolque_1 > 150000):
                raise UserError(_('Alerta !\nEl peso destino del remolque 1 debe estar entre 1 y 150,000.'))

            if self.peso_destino_remolque_2 > 0 and (self.peso_destino_remolque_2 > 150000):
                raise UserError(_('Alerta !\nEl peso destino del remolque 2 debe estar entre 1 y 150,000.'))

            if self.peso_convenido_remolque_1 > 0 and (self.peso_convenido_remolque_1 > 150000):
                raise UserError(_('Alerta !\nEl peso convenido del remolque 1 debe estar entre 1 y 150,000.'))

            if self.peso_convenido_remolque_2 > 0 and (self.peso_convenido_remolque_2 > 150000):
                raise UserError(_('Alerta !\nEl peso convenido del remolque 2 debe estar entre 1 y 150,000.'))
            
            if (self.peso_autorizado <= 0) or (self.peso_autorizado > 150000):
                raise UserWarning(_('Alerta !\nEl peso autorizado debe estar entre 1 y 150,000 toneladas.'))
            
        #--------------------------------------------
        #Licitación.
        #--------------------------------------------
        #if self.asociado_id.para_licitacion:
        #    if not self.asociado_id.para_licitacion_aprobado:
        #        raise UserError(_('El asociado no esta aprobado para licitación.'))
        
        #if self.operador_id.para_licitacion:
        #    if not self.operador_id.para_licitacion_aprobado:
        #        raise UserError(_('El operador no esta aprobado para licitación.'))

        #if self.placas_id.para_licitacion:
        #    if not self.placas_id.para_licitacion_aprobado:
        #        raise UserError(_('El vehículo no esta aprobado para licitación.'))

    @api.constrains('tarifa_asociado')
    def _check_tarifa_asociado(self):
        if self.tarifa_asociado <= 0:
            raise UserError(_('Aviso !\nLa tarifa asociado debe ser mayor a 0'))

        # if self.tarifa_asociado > self.tarifa_cliente:
        #    raise UserError(_('Aviso !\nLa tarifa asociado no puede ser mayor a la tarifa cliente'))

        obj = self.env['trafitec.cotizacion.linea.negociacion'].search(
            [('linea_id', '=', self.linea_id.id), ('asociado_id', '=', self.asociado_id.id), ('state', '=', 'autorizado')])
        print("**********VIAJE LINEAS" + str(obj))
        if len(obj) > 0:
            for nego in obj:
                if self.tarifa_asociado > nego.tarifa:
                    raise UserError(_('Aviso !\nLa tarifa asociado no puede ser mayor a la tarifa asociado de la negociación.'))
        elif self.tarifa_asociado > self.linea_id.tarifa_asociado:
            raise UserError(_('Aviso !\nLa tarifa asociado no puede ser mayor a la tarifa asociado de la cotización.'))

    @api.constrains('tarifa_cliente', 'tarifa_asociado')
    def _check_tarifa_cliente(self):
        context = self._context
        if context.get('validar_tc', True):
            if self.tarifa_cliente <= 0:
                raise UserError(_('Aviso !\nLa tarifa cliente debe ser mayor a 0'))
            if self.tarifa_cliente < self.linea_id.tarifa_cliente:
                raise UserError(_('Aviso !\nLa tarifa cliente no puede ser menor a la tarifa cliente de la cotizacion'))
    
            infocliente = self.env['res.partner'].search([('id', '=', self.cliente_id.id)])
            if (not infocliente.permitir_ta_mayor_tc) and self.tarifa_asociado > self.tarifa_cliente:
                raise UserError(_('Alerta..\nLa tarifa asociado no puede ser mayor a la tarifa cliente'))

    
    @api.depends('facturar_con', 'facturar_con_cliente', 'peso_destino_remolque_1', 'peso_destino_remolque_2',
                'peso_convenido_remolque_1', 'peso_convenido_remolque_2', 'peso_origen_remolque_1',
                'peso_origen_remolque_2', 'tarifa_asociado', 'tarifa_cliente')
    def _compute_flete(self):
        for reg in self:
            if reg.facturar_con:
                if reg.facturar_con == 'Peso convenido':
                    reg.flete_asociado = (reg.peso_convenido_total / 1000) * reg.tarifa_asociado
                elif reg.facturar_con == 'Peso origen':
                    reg.flete_asociado = (reg.peso_origen_total / 1000) * reg.tarifa_asociado
                elif reg.facturar_con == 'Peso destino':
                    reg.flete_asociado = (reg.peso_destino_total / 1000) * reg.tarifa_asociado
            else:
                reg.flete_asociado = 0

            if reg.facturar_con_cliente:
                if reg.facturar_con_cliente == 'Peso convenido':
                    reg.flete_cliente = (reg.peso_convenido_total / 1000) * reg.tarifa_cliente
                elif reg.facturar_con_cliente == 'Peso origen':
                    reg.flete_cliente = (reg.peso_origen_total / 1000) * reg.tarifa_cliente
                elif reg.facturar_con_cliente == 'Peso destino':
                    reg.flete_cliente = (reg.peso_destino_total / 1000) * reg.tarifa_cliente
            else:
                reg.flete_cliente = 0

    flete_cliente = fields.Float(string='Flete cliente', store=True, readonly=True, compute='_compute_flete')

    flete_asociado = fields.Float(string='Flete asociado', store=True, readonly=True, compute='_compute_flete')

    pronto_pago = fields.Boolean(sring='Pronto pago', default=False)

    flete_diferencia = fields.Float('Dieferencia en flete', compute='_compute_flete_diferencia', store=True)

    
    @api.depends('flete_cliente', 'flete_asociado')
    def _compute_flete_diferencia(self):
        self.flete_diferencia = self.flete_cliente - self.flete_asociado

    

    @api.onchange('linea_id')
    def _onchange_subpedido(self):
        print("**********SUBPEDIDO" + str(self.linea_id))
        if self.linea_id:
            self.tarifa_cliente = self.linea_id.tarifa_cliente
            self.facturar_con = self.linea_id.cotizacion_id.cliente.facturar_con
            self.facturar_con_cliente = self.linea_id.cotizacion_id.cliente.facturar_con
            self.excedente_merma = self.linea_id.cotizacion_id.cliente.excedente_merma
            self.lineanegocio = self.linea_id.cotizacion_id.lineanegocio  # Mike.

            self.cliente_id = self.linea_id.cotizacion_id.cliente  # Mike
            self.origen = self.origen  # Mike
            self.destino = self.destino  # Mike

            if self.linea_id.name:
                self.folio_cliente = self.linea_id.name

            self.costo_producto = self.linea_id.cotizacion_id.costo_producto
            
            #Seguro de carga.
            if self.linea_id.cotizacion_id.polizas_seguro:
                #Si no tiene seguro y no hay seguro en tarifa.
                if not self.seguro_id:
                    self.seguro_id = self.linea_id.cotizacion_id.polizas_seguro
                    self.costo_producto = self.linea_id.cotizacion_id.costo_producto
                    self.seguro_pcliente = self.linea_id.cotizacion_id.porcen_seguro
                    self.seguro_entarifa = self.linea_id.cotizacion_id.seguro_entarifa

    @api.onchange('seguro_id')
    def _onchange_seguro(self):
        print(":::::MIKE::::Si entro onchange seguro")
        if self.seguro_id:
            self.seguro_pcliente = self.linea_id.cotizacion_id.porcen_seguro
        else:
            self.seguro_pcliente = 0
            self.seguro_total = 0
    
    @api.onchange('lineanegocio')
    def _onchange_lineanegocio(self):
        if self.lineanegocio:
            if self.lineanegocio.id == 3:
                if self.tipo_remolque.tipo == 'sencillo':
                    self.peso_origen_remolque_1 = 1000
                    self.peso_origen_remolque_2 = 0
                    self.peso_destino_remolque_1 = 1000
                    self.peso_destino_remolque_2 = 0
                else:
                    self.peso_origen_remolque_1 = 500
                    self.peso_origen_remolque_2 = 500
                    self.peso_destino_remolque_1 = 500
                    self.peso_destino_remolque_2 = 500
            else:
                self.peso_origen_remolque_1 = 0
                self.peso_origen_remolque_2 = 0
                self.peso_destino_remolque_1 = 0
                self.peso_destino_remolque_2 = 0

    @api.onchange('linea_id', 'asociado_id')
    def _onchange_tarifa(self):
        if self.linea_id and self.asociado_id:
            obj_nego = self.env['trafitec.cotizacion.linea.negociacion'].search(
                [('linea_id', '=', self.linea_id.id), ('asociado_id', '=', self.asociado_id.id)])
            if len(obj_nego) > 0:
                self.tarifa_asociado = obj_nego.tarifa
            else:
                self.tarifa_asociado = self.linea_id.tarifa_asociado

    def traduce_account_invoice_state(self, state):
        valores = {
            'draft': _('Borrador'),
            'proforma': _('Proforma'),
            'proforma2': _('Proforma2'),
            'open': _('Abierto'),
            'paid': _('Pagado'),
            'cancel': _('Cancelado')
        }
        
        return valores.get(state, '')
    
    
    @api.depends("contrarecibo_id", "contrarecibo_id.state", "en_contrarecibo", "factura_cliente_id", "factura_cliente_id.state", "en_factura")
    def _compute_info(self):
        info = ""
        try:
            #self._fields['your_field']._desription_selection(self.env)
            #dict(self._fields['type'].selection).get(self.type)
            
            cr = self.contrarecibo_id
            cp = cr.invoice_id
            f = self.factura_cliente_id
        
            info += "CR: " + (cr.name or "") + " " + (cr.fecha or "") + " " + (cr.state or "") + "  "
            info += "CP: " + (cp.name or "") + " " + (cp.ref or "") + " " + (cp.date or "") + " " + (self.traduce_account_invoice_state(cp.state) or "") + "  "
            info += "F:  " + (f.name or "") + " " + (f.date or "") + " " + (self.traduce_account_invoice_state(f.state) or "") + "  "
        except:
            _logger.info("SLI_TRAFITEC: Error al calcular Info de viajes.")
        
        self.info = info

    # Transporte
    placas_id = fields.Many2one('fleet.vehicle', string='Placas', required=True)
    vehiculo = fields.Char(string='Vehiculo', readonly=True, track_visibility='onchange')
    asociado_id = fields.Many2one(related='placas_id.asociado_id', string='Asociado', store=True)
    porcentaje_comision = fields.Float(string='Porcentaje de comisión', readonly=True)
    usar_porcentaje = fields.Boolean(string='Usar porcentaje de línea de negocio', readonly=True)
    creditocomision = fields.Boolean(string='Crédito de comisión', readonly=True)
    operador_id = fields.Many2one('res.partner', string="Operador", required=True,domain="[('operador','=',True)]")
    no_economico = fields.Char(string='No. economico', readonly=True, related='placas_id.numero_economico')
    celular_asociado = fields.Char(string='Celular asociado', required=True)
    tipo_camion = fields.Selection([("Jaula", "Jaula"), ("Caja Seca", "Caja Seca"), ("Portacontenedor", "Portacontenedor"), ("Tolva", "Tolva"), ("Plataforma", "Plataforma"), ("Gondola", "Gondola"), ("Torton", "Torton"), ("Rabon", "Rabon"), ("Chasis", "Chasis"), ("Thermo 48", "Thermo 48"), ("Thermo 53", "Thermo 53")], string='Tipo remolque')

    tipo_remolque = fields.Many2one('trafitec.moviles', string='Tipo de remolque',
                                    domain="['|',('lineanegocio','=',lineanegocio),('lineanegocio','=',False)]")
    nombre_remolque = fields.Selection([('full', 'Full'), ('sencillo', 'Sencillo')], string="Tipo",
                                    related='tipo_remolque.tipo')
    capacidad = fields.Float(string="Capacidad", related='tipo_remolque.capacidad', readonly=True, store=True)
    tipo = fields.Selection([('full', 'Full'), ('sencillo', 'Sencillo')], string="Tipo", related='tipo_remolque.tipo',
                            readonly=True, store=True,
                            track_visibility='onchange')  # Define si el remolque es full o sencillo
    celular_operador = fields.Char(string='Celular operador', required=True)


    info = fields.Text(string='Información', compute='_compute_info', store=False)

    #Para pasar a la bd de Flotta.
    costo_km_vacio = fields.Float(string='Costo por km vacío', default=0, help='Costo por kilómetro vacío.')
    costo_km_cargado = fields.Float(string='Costo por km cargado', default=0, help='Costo por kilómetro cargado.')
    
        
    
    @api.depends('flete_cliente', 'flete_asociado')
    def _compute_utilidad_txt(self):
        if self.flete_cliente <= 0 and self.flete_asociado <= 0:
            self.utilidad_txt = "--"
            return
                    
        #Calculos.
        utilidad = self.flete_cliente-self.flete_asociado
        cantidad = self.flete_cliente*0.05 #Cinco porciento.
        if utilidad >= cantidad:
            self.utilidad_txt = "si"
        else:
            self.utilidad_txt = "no"
        
    
    utilidad_txt=fields.Selection(string='Utilidad', compute='_compute_utilidad_txt',selection=[('no','NO'),('si','SI'),('--','--')],default='--',store=True)
    

    #--------------------------------------------------------------------------------------------------------------------------------------
    #SLI TRACK
    #--------------------------------------------------------------------------------------------------------------------------------------
    slitrack_gps_latitud = fields.Float(string='Latitud slitrack', default=0, digits=(10, 10))
    slitrack_gps_longitud = fields.Float(string='Longitud slitrack', default=0, digits=(10, 10))
    slitrack_gps_velocidad = fields.Float(string='Velocidad slitrack', default=0)
    slitrack_gps_fechahorar = fields.Datetime(string='Fecha y hora slitrack')
    slitrack_comentarios = fields.Text(string='Comentarios slitrack', defaut='')
    slitrack_estado = fields.Selection(string='Estado slitrack', selection=[('noiniciado', '(No iniciado)'), ('iniciado', 'Iniciado'),('terminado', 'Terminado')], default='noiniciado')
    slitrack_codigo = fields.Char(string='Código slitrack', default='')
    slitrack_gps_contador = fields.Integer(string='Contador slitrack', default=0)
    slitrack_st = fields.Selection(string='Activo slitrack', selection=[('inactivo', 'Inactivo'), ('activo', 'Activo')],default='inactivo')

    slitrack_registro=fields.One2many(string='Registro slitrack', comodel_name='trafitec.slitrack.registro',inverse_name='viaje_id')
    slitrack_proveedor=fields.Selection(string="Tip slitrack", selection=[('slitrack','SLI Track'),('geotab','GeoTab'),('manual','Manual')],default='manual')
    
    def action_slitrack_codigo(self):
        codigo = str(self.id)+str(random.randrange(10000, 99999))
        #self.slitrack_codigo = codigo
        self.with_context(validar_credito_cliente=False).write({'slitrack_codigo': codigo})

    def action_slitrack_activa(self):
        self.action_slitrack_codigo()
        self.slitrack_estado = 'noiniciado'
        self.slitrack_st = 'activo'
        
    #--------------------------------------------------------------------------------------------------------------------------------------

    @api.onchange('asociado_id')
    def _onchange_asociado(self):
        if self.asociado_id:
            if self.asociado_id.mobile:
                self.celular_asociado = self.asociado_id.mobile
            elif self.asociado_id.phone:
                self.celular_asociado = self.asociado_id.phone

    @api.onchange('operador_id')
    def _onchange_operador(self):
        if self.operador_id:
            if self.operador_id.mobile:
                self.celular_operador = self.operador_id.mobile
            elif self.operador_id.phone:
                self.celular_operador = self.operador_id.phone

    @api.onchange('placas_id')
    def _vehiculo_(self):
        if self.placas_id:
            self.asociado_id = self.placas_id.asociado_id
            self.porcentaje_comision = self.placas_id.asociado_id.porcentaje_comision
            self.usar_porcentaje = self.placas_id.asociado_id.usar_porcentaje
            self.creditocomision = self.placas_id.asociado_id.creditocomision
            self.operador_id = self.placas_id.operador_id
            self.no_economico = self.placas_id.no_economico
            marca = self.placas_id.name
            if self.placas_id.modelo:
                modelo = self.placas_id.modelo
            else:
                modelo = ''
            if self.placas_id.color:
                color = self.placas_id.color
            else:
                color = ''
            str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
            self.vehiculo = str_vehiculo

    # Comision
    regla_comision = fields.Selection([('No cobrar', 'No cobrar'),
                                        ('Con % linea transportista y peso origen',
                                            'Con % linea transportista y peso origen'),
                                        ('Con % linea transportista y peso destino',
                                            'Con % linea transportista y peso destino'),
                                        ('Con % linea transportista y peso convenido',
                                            'Con % linea transportista y peso convenido'),
                                        ('Con % linea transportista y capacidad de remolque',
                                            'Con % linea transportista y capacidad de remolque'),
                                        ('Con % especifico y peso origen', 'Con % especifico y peso origen'),
                                        ('Con % especifico y peso destino', 'Con % especifico y peso destino'),
                                        ('Con % especifico y peso convenido', 'Con % especifico y peso convenido'),
                                        ('Con % especifico y capacidad de remolque',
                                            'Con % especifico y capacidad de remolque'),
                                        ('Cobrar cantidad especifica', 'Cobrar cantidad específica')],
                                        string='Regla de Comisión', default='Con % linea transportista y peso origen',
                                        required=True, track_visibility='onchange')
    comision = fields.Selection([('No cobrar', 'No cobrar'), ('Cobrar en contra-recibo', 'Cobrar en contra-recibo'), (
    'Cobrar en contra recibo-porcentaje especifico', 'Cobrar en contra recibo-porcentaje específico'),
                                ('Cobrar cantidad especifica', 'Cobrar cantidad específica')], string='Comisión',
                                default='Cobrar en contra-recibo', required=True, track_visibility='onchange')
    motivo = fields.Text(string='Motivo sin comisión', track_visibility='onchange')
    porcent_comision = fields.Float(string='Porcentaje de comisión')
    cant_especifica = fields.Float(string='Cobrar cantidad específica')
    peso_autorizado = fields.Float(string='Peso autorizado (Kg)', required=True, help='Peso autorizado en toneladas.')
    tipo_viaje = fields.Selection([('Normal', 'Normal'), ('Directo', 'Directo'), ('Cobro destino', 'Cobro destino')],
                                string='Tipo de viaje', default='Normal', required=True)
    maniobras = fields.Float(string='Maniobras')
    regla_maniobra = fields.Selection(
        [('Pagar en contrarecibo y cobrar en factura', 'Pagar en contrarecibo y cobrar en factura'),
            ('Pagar en contrarecibo y no cobrar en factura', 'Pagar en contrarecibo y no cobrar en factura'),
            ('No pagar en contrarecibo y cobrar en factura', 'No pagar en contrarecibo y cobrar en factura'),
            ('No pagar en contrarecibo y no cobrar en factura', 'No pagar en contrarecibo y no cobrar en factura')],
        string='Regla de maniobra', default='Pagar en contrarecibo y cobrar en factura', required=True,
        track_visibility='onchange')

    @api.onchange('regla_comision', 'cant_especifica', 'facturar_con', 'regla_comision')
    def _onchange_comision_calculada(self):
        if self.regla_comision == 'No cobrar':
            self.comision_calculada = 0
        elif self.regla_comision == 'Cobrar cantidad especifica':
            self.comision_calculada = self.cant_especifica
        else:
            peso = 0
            if self.facturar_con == 'Peso convenido':
                peso = self.peso_convenido_total
            elif self.facturar_con == 'Peso origen':
                peso = self.peso_origen_total
            elif self.facturar_con == 'Peso destino':
                peso = self.peso_destino_total
            if self.usar_porcentaje == True:
                linea_tran = (self.comision_linea / 100)
            else:
                linea_tran = (self.porcentaje_comision / 100)
            if peso != 0 or peso is not None:
                pesototal_asociado = (peso / 1000) * self.tarifa_asociado
                if self.regla_comision == 'Con % linea transportista y peso origen' or self.regla_comision == 'Con % linea transportista y peso destino' or self.regla_comision == 'Con % linea transportista y peso convenido':
                    self.comision_calculada = pesototal_asociado * linea_tran
                if self.regla_comision == 'Con % linea transportista y capacidad de remolque':
                    self.comision_calculada = ((self.capacidad / 1000) * self.tarifa_asociado) * linea_tran

                if self.regla_comision == 'Con % especifico y peso origen' or self.regla_comision == 'Con % especifico y peso destino' or self.regla_comision == 'Con % especifico y peso convenido':
                    self.comision_calculada = pesototal_asociado * (self.porcent_comision / 100)
                if self.regla_comision == 'Con % especifico y capacidad de remolque':
                    self.comision_calculada = ((self.capacidad / 1000) * self.tarifa_asociado) * (
                    self.porcent_comision / 100)

    
    def _compute_comision_calculada(self):
        if self.regla_comision == 'No cobrar':
            self.comision_calculada = 0
        elif self.regla_comision == 'Cobrar cantidad especifica':
            self.comision_calculada = self.cant_especifica
        else:
            peso = 0
            if self.facturar_con == 'Peso convenido':
                peso = self.peso_convenido_total
            elif self.facturar_con == 'Peso origen':
                peso = self.peso_origen_total
            elif self.facturar_con == 'Peso destino':
                peso = self.peso_destino_total
            if self.usar_porcentaje == True:
                linea_tran = (self.comision_linea / 100)
            else:
                linea_tran = (self.porcentaje_comision / 100)
            if peso != 0 or peso is not None:
                pesototal_asociado = (peso / 1000) * self.tarifa_asociado
                if self.regla_comision == 'Con % linea transportista y peso origen' or self.regla_comision == 'Con % linea transportista y peso destino' or self.regla_comision == 'Con % linea transportista y peso convenido':
                    self.comision_calculada = pesototal_asociado * linea_tran
                if self.regla_comision == 'Con % linea transportista y capacidad de remolque':
                    self.comision_calculada = ((self.capacidad / 1000) * self.tarifa_asociado) * linea_tran

                if self.regla_comision == 'Con % especifico y peso origen' or self.regla_comision == 'Con % especifico y peso destino' or self.regla_comision == 'Con % especifico y peso convenido':
                    self.comision_calculada = pesototal_asociado * (self.porcent_comision / 100)
                if self.regla_comision == 'Con % especifico y capacidad de remolque':
                    self.comision_calculada = ((self.capacidad / 1000) * self.tarifa_asociado) * (
                    self.porcent_comision / 100)
        if self.comision_calculada > 0:
            valores = {'viaje_id': self.id, 'monto': self.comision_calculada, 'tipo_cargo': 'comision',
                        'asociado_id': self.asociado_id.id}
            obc_cargos = self.env['trafitec.cargos'].search(
                ['&', ('viaje_id', '=', self.id), ('tipo_cargo', '=', 'comision')])
            if len(obc_cargos) == 0:
                self.env['trafitec.cargos'].create(valores)
            else:
                obc_cargos.write(valores)

                # Genera el cargo por comision.
                # obj_cargo=self.env['trafitec.cargosx'].search([('viaje_id','=',self.id)])
                # cargo_nuevo={'viaje_id':self.id,'asociado_id':self.asociado_id.id,'total':self.comision_calculada,'abonos':0,'saldo':0,'tipo':'comision'}
                # if len(obj_cargo)==1: #Si existe lo actualiza.
                #    obj_cargo.write(cargo_nuevo)
                # else: #Si no existe lo crea.
                #    obj_cargo.create(cargo_nuevo)

    comision_calculada = fields.Float(string='Comisión calculada', compute='_compute_comision_calculada', readonly=True)

    # carta de instruccion
    detalle_asociado = fields.Text(string='Detalle Origen', related='linea_id.detalle_asociado',
                                    store=True)
    detalle_destino = fields.Text(string='Detalle Destino', related='linea_id.detalle_destino', store=True)

    # Cita
    fecha_hora_carga = fields.Datetime(string='Fecha y hora carga')
    fecha_hora_descarga = fields.Datetime(string='Fecha y hora descarga')
    detalles_cita = fields.Text(string='Detalles cita')

    # detalles
    observaciones = fields.Text(string='Observaciones', track_visibility='onchange')
    especificaciones = fields.Text(string='Especificaciones', track_visibility='onchange')
    folio_cliente = fields.Char(string='Folio del cliente', track_visibility='onchange')
    suger_pago = fields.Boolean(string='Sugerir pago inmediato', track_visibility='onchange')
    # contenedores
    no_pedimento = fields.Char(string='No. de pedimento')
    tipo_mov = fields.Selection(
        [('No especificado', 'No especificado'), ('Importación', 'Importación'), ('Exportación', 'Exportación')],
        string='Tipo de movimiento')
    no_contenedor_uno = fields.Char(string='No de contenedor 1')
    no_sello_uno = fields.Char(string='No. Sello 1')
    tipo_contenedor_uno = fields.Selection(
        [('No especificado', 'No especificado'), ('Seco', 'Seco'), ('Refrigerado', 'Refrigerado')],
        string='Tipo de contenedor 1')
    tamano_contenedor_uno = fields.Selection(
        [('No especificado', 'No especificado'), ('40 pies', '40 pies'), ('40 pies HC', '40 pies HC'),
            ('20 pies', '20 pies'), ('20 pies HC', '20 pies HC')], string='Tamaño de contenedor 1')
    no_contenedor_dos = fields.Char(string='No de contenedor 2')
    no_sello_dos = fields.Char(string='No. Sello 2')
    tipo_contenedor_dos = fields.Selection(
        [('No especificado', 'No especificado'), ('Seco', 'Seco'), ('Refrigerado', 'Refrigerado')],
        string='Tipo de contenedor 2')
    tamano_contenedor_dos = fields.Selection(
        [('No especificado', 'No especificado'), ('40 pies', '40 pies'), ('40 pies HC', '40 pies HC'),
            ('20 pies', '20 pies'), ('20 pies HC', '20 pies HC')], string='Tamaño de contenedor 2')

    @api.onchange('tipo_remolque','lineanegocio')
    def _onchange_pesos_(self):
        if self.lineanegocio.id == 1:  # Granel.
            self.peso_origen_remolque_1 = 0
            self.peso_origen_remolque_2 = 0
            
            self.peso_destino_remolque_1 = 0
            self.peso_destino_remolque_2 = 0
            
            self.peso_convenido_remolque_1 = 0
            self.peso_convenido_remolque_2 = 0


        if self.lineanegocio.id == 2 or self.lineanegocio.id == 3:  # Flete y Contenedores.
            if self.tipo_remolque.tipo == 'sencillo': #Si es sencillo.

                self.peso_origen_remolque_1 = 1000
                self.peso_origen_remolque_2 = 0

                self.peso_destino_remolque_1 = 1000
                self.peso_destino_remolque_2 = 0

                self.peso_convenido_remolque_1 = 1000
                self.peso_convenido_remolque_2 = 0

            else:  # Si es Full.
                self.peso_origen_remolque_1 = 500
                self.peso_origen_remolque_2 = 500

                self.peso_destino_remolque_1 = 500
                self.peso_destino_remolque_2 = 500

                self.peso_convenido_remolque_1 = 500
                self.peso_convenido_remolque_2 = 500


            

    peso_origen_remolque_1 = fields.Float(string='Peso remolque 1 Kg', help='Peso origen del remolque 1 en kilogramos.', track_visibility='onchange')
    peso_origen_remolque_2 = fields.Float(string='Peso remolque 2 Kg', help='Peso origen del remolque 2 en kilogramos.', track_visibility='onchange')
    peso_destino_remolque_1 = fields.Float(string='Peso remolque 1 Kg', help='Peso destino del remolque 1 en kilogramos.', track_visibility='onchange')
    peso_destino_remolque_2 = fields.Float(string='Peso remolque 2 Kg', help='Peso destino del remolque 2 en kilogramos.', track_visibility='onchange')
    peso_convenido_remolque_1 = fields.Float(string='Peso remolque 1 Kg', help='Peso convenido del remolque 1 en kilogramos.', track_visibility='onchange')
    peso_convenido_remolque_2 = fields.Float(string='Peso remolque 2 Kg', help='Peso convenido del remolque 2 en kilogramos.', track_visibility='onchange')

    peso_origen_remolque_1_ver = fields.Float(string='Peso remolque 1 Kg', related='peso_origen_remolque_1', readonly=True)
    peso_origen_remolque_2_ver = fields.Float(string='Peso remolque 2 Kg', related='peso_origen_remolque_2', readonly=True)
    peso_destino_remolque_1_ver = fields.Float(string='Peso remolque 1 Kg', related='peso_destino_remolque_1', readonly=True)
    peso_destino_remolque_2_ver = fields.Float(string='Peso remolque 2 Kg', related='peso_destino_remolque_2', readonly=True)
    peso_convenido_remolque_1_ver = fields.Float(string='Peso remolque 1 Kg', related='peso_convenido_remolque_1', readonly=True)
    peso_convenido_remolque_2_ver = fields.Float(string='Peso remolque 2 Kg', related='peso_convenido_remolque_2', readonly=True)


    
    @api.depends('peso_origen_remolque_1','peso_origen_remolque_2')
    def _compute_pesos_origen_total(self):
            self.peso_origen_total = self.peso_origen_remolque_1 + self.peso_origen_remolque_2

    
    @api.depends('peso_destino_remolque_1','peso_destino_remolque_2')
    def _compute_pesos_destino_total(self):
            self.peso_destino_total = self.peso_destino_remolque_1 + self.peso_destino_remolque_2

    
    @api.depends('peso_convenido_remolque_1','peso_convenido_remolque_2')
    def _compute_pesos_convenido_total(self):
            self.peso_convenido_total = self.peso_convenido_remolque_1 + self.peso_convenido_remolque_2


    peso_origen_total = fields.Float(string='Peso total Kg', compute='_compute_pesos_origen_total',store=True)
    peso_destino_total = fields.Float(string='Peso total Kg', compute='_compute_pesos_destino_total',store=True)
    peso_convenido_total = fields.Float(string='Peso total Kg', compute='_compute_pesos_convenido_total',store=True)
    
    
    facturar_con = fields.Selection(
        [('Peso convenido', 'Peso convenido'), ('Peso origen', 'Peso origen'), ('Peso destino', 'Peso destino')],
        string='Facturar con (Asociado)', required=True, default='Peso origen', track_visibility='onchange')

    facturar_con_cliente = fields.Selection(
        [('Peso convenido', 'Peso convenido'), ('Peso origen', 'Peso origen'), ('Peso destino', 'Peso destino')],
        string='Facturar con (Cliente)', required=True, default='Peso origen', track_visibility='onchange')
    excedente_merma = fields.Selection(
        [('No cobrar', 'No cobrar'), ('Porcentaje: Cobrar diferencia', 'Porcentaje: Cobrar diferencia'),
            ('Porcentaje: Cobrar todo', 'Porcentaje: Cobrar todo'), ('Kg: Cobrar diferencia', 'Kg: Cobrar diferencia'),
            ('Kg: Cobrar todo', 'Kg: Cobrar todo'), ('Cobrar todo', 'Cobrar todo')],
        string='Si la merma excede lo permitido', required=True, default='Porcentaje: Cobrar diferencia')

    # @api.constrains('peso_origen_remolque_1','peso_origen_remolque_2','peso_destino_remolque_1','peso_destino_remolque_2','peso_convenido_remolque_1','peso_convenido_remolque_2','peso_convenido_remolque_1','peso_convenido_remolque_2')
    # def _check_origen_remolque1(self):
    #    for record in self:
    #        if record.peso_origen_remolque_1 < 0 or record.peso_origen_remolque_2 < 0 or record.peso_destino_remolque_1  < 0 or record.peso_destino_remolque_2 < 0 or record.peso_convenido_remolque_1 < 0 or record.peso_convenido_remolque_2 < 0:
    #            raise ValidationError("No se permite valores en negativo en los pesos del viaje")

    @api.onchange('peso_origen_total', 'peso_destino_total')
    def _onchange_merma_kg_(self):
        self.merma_kg = 0
        if self.peso_origen_total and self.peso_destino_total:
            if self.peso_destino_total > self.peso_origen_total:
                self.merma_kg = 0
            else:
                self.merma_kg = self.peso_origen_total - self.peso_destino_total
        else:
            self.merma_kg = 0

    
    def _compute_merma_kg_(self):
        self.merma_kg = 0
        if self.peso_origen_total and self.peso_destino_total:
            if self.peso_destino_total > self.peso_origen_total:
                self.merma_kg = 0
            else:
                self.merma_kg = self.peso_origen_total - self.peso_destino_total
        else:
            self.merma_kg = 0

    merma_kg = fields.Float(string='Merma Kg', compute='_compute_merma_kg_', readonly=True)

    @api.onchange('peso_origen_total', 'peso_destino_total', 'tipo_remolque')
    def _onchange_merma_pesos(self):
        if self.peso_origen_total and self.peso_destino_total:
            # if 'Contenedor' in self.tipo_remolque.name:
            if self.lineanegocio.id == 3:  # Contenedores.
                self.merma_pesos = 0
            else:
                self.merma_pesos = (self.merma_kg) * self.costo_producto
        else:
            self.merma_pesos = 0

    @api.depends('merma_kg')
    
    def _compute_merma_pesos(self):
        if self.peso_origen_total and self.peso_destino_total:
            if self.lineanegocio.id == 3:  # Contenedores.
                self.merma_pesos = 0
            else:
                self.merma_pesos = (self.merma_kg / 1000) * self.costo_producto
        else:
            self.merma_pesos = 0

    merma_pesos = fields.Float(string='Merma $', compute='_compute_merma_pesos', readonly=True)

    @api.onchange('excedente_merma', 'peso_origen_total', 'peso_destino_total')
    def _onchange_merma_permitida_kg(self):
        if self.peso_origen_total and self.peso_destino_total:
            if self.excedente_merma:
                if self.excedente_merma == 'No cobrar':
                    self.merma_permitida_kg = 0
                else:
                    if self.cliente_id.merma_permitida_por:
                        if self.peso_origen_total > self.peso_destino_total:
                            self.merma_permitida_kg = self.cliente_id.merma_permitida_por * (
                            self.peso_origen_total / 100)
                        else:
                            self.merma_permitida_kg = 0
        else:
            self.merma_permitida_kg = 0

    @api.onchange('peso_origen_remolque_1', 'peso_origen_remolque_2', 'peso_destino_remolque_1',
                    'peso_destino_remolque_2')
    def _calcula_cargosx(self):
        pesoo_r1 = 0
        pesoo_r2 = 0
        pesod_r1 = 0
        pesod_r2 = 0
        pesoo = 0
        pesod = 0

        merma_kg = 0
        merma_m = 0

        merma_c_kg = 0
        merma_c_m = 0

        if self.peso_origen_remolque_1:
            pesoo_r1 = self.peso_origen_remolque_1

        if self.peso_origen_remolque_2:
            pesoo_r2 = self.peso_origen_remolque_2

        if self.peso_destino_remolque_1:
            pesod_r1 = self.peso_destino_remolque_1

        if self.peso_destino_remolque_2:
            pesod_r2 = self.peso_destino_remolque_2

        if pesoo_r1 > 0 and pesod_r1 > 0 and pesoo_r1 > pesod_r1:
            merma_kg += pesoo_r1 - pesod_r1

        if pesoo_r2 > 0 and pesod_r2 > 0 and pesoo_r2 > pesod_r2:
            merma_kg += pesoo_r2 - pesod_r2

        pesoo = pesoo_r1 + pesoo_r2
        pesod = pesod_r1 + pesod_r2

        print("**********MERMA KG: " + str(merma_kg))

    
    def _compute_merma_permitida_kg(self):
        if self.peso_origen_total and self.peso_destino_total:
            if self.excedente_merma:
                if self.excedente_merma == 'No cobrar':
                    self.merma_permitida_kg = 0
                else:
                    if self.cliente_id.merma_permitida_por:
                        if self.peso_origen_total > self.peso_destino_total:
                            self.merma_permitida_kg = self.cliente_id.merma_permitida_por * (
                            self.peso_origen_total / 100)
                        else:
                            self.merma_permitida_kg = 0
        else:
            self.merma_permitida_kg = 0

    merma_permitida_kg = fields.Float(string='Merma permitida Kg', compute='_compute_merma_permitida_kg', readonly=True)

    @api.onchange('merma_permitida_kg', 'costo_producto')
    def _onchange_merma_permitida_pesos(self):
        if self.peso_origen_total and self.peso_destino_total:
            if self.merma_permitida_kg:
                self.merma_permitida_pesos = (self.merma_permitida_kg) * self.costo_producto
            else:
                self.merma_permitida_pesos = 0
        else:
            self.merma_permitida_pesos = 0

    
    def _compute_merma_permitida_pesos(self):
        if self.peso_origen_total and self.peso_destino_total:
            if self.merma_permitida_kg:
                self.merma_permitida_pesos = (self.merma_permitida_kg ) * self.costo_producto
            else:
                self.merma_permitida_pesos = 0
        else:
            self.merma_permitida_pesos = 0

    merma_permitida_pesos = fields.Float(string='Merma permitida $', compute='_compute_merma_permitida_pesos',
                                        readonly=True)

    @api.onchange('peso_origen_remolque_1', 'peso_origen_remolque_2', 'peso_destino_remolque_1',
                    'peso_destino_remolque_2')
    def _onchange_merma_total(self):
        if self.peso_origen_remolque_1 > self.peso_destino_remolque_1:
            merma_origen = self.peso_origen_remolque_1 - self.peso_destino_remolque_1
        else:
            merma_origen = 0
        if self.peso_origen_remolque_2 > self.peso_destino_remolque_2:
            merma_destino = self.peso_origen_remolque_2 - self.peso_destino_remolque_2
        else:
            merma_destino = 0
        self.merma_total = merma_origen + merma_destino

    
    def _compute_merma_total(self):
        if self.peso_origen_remolque_1 > self.peso_destino_remolque_1:
            merma_origen = self.peso_origen_remolque_1 - self.peso_destino_remolque_1
        else:
            merma_origen = 0
        if self.peso_origen_remolque_2 > self.peso_destino_remolque_2:
            merma_destino = self.peso_origen_remolque_2 - self.peso_destino_remolque_2
        else:
            merma_destino = 0
        self.merma_total = merma_origen + merma_destino

    merma_total = fields.Float(string='Merma total kg', compute='_compute_merma_total', readonly=True)

    @api.onchange('merma_kg', 'merma_permitida_kg')
    def _onchange_diferencia_porcentaje(self):
        if self.merma_kg > self.merma_permitida_kg:
            self.diferencia_porcentaje = self.merma_kg - self.merma_permitida_kg
        else:
            self.diferencia_porcentaje = 0

    
    def _compute_diferencia_porcentaje(self):
        if self.merma_kg > self.merma_permitida_kg:
            self.diferencia_porcentaje = self.merma_kg - self.merma_permitida_kg
        else:
            self.diferencia_porcentaje = 0

    diferencia_porcentaje = fields.Float(string='diferencia_porcentaje kg', compute='_compute_diferencia_porcentaje',
                                        readonly=True)

    @api.onchange('merma_kg', 'cliente_id')
    def _onchange_diferencia_kg(self):
        if self.merma_kg > self.cliente_id.merma_permitida_kg:
            self.diferencia_kg = self.merma_kg - self.cliente_id.merma_permitida_kg
        else:
            self.diferencia_kg = 0

    
    def _compute_diferencia_kg(self):
        if self.merma_kg > self.cliente_id.merma_permitida_kg:
            self.diferencia_kg = self.merma_kg - self.cliente_id.merma_permitida_kg
        else:
            self.diferencia_kg = 0

    diferencia_kg = fields.Float(string='diferencia_porcentaje kg', compute='_compute_diferencia_kg',
                                readonly=True)

    @api.onchange('excedente_merma', 'merma_permitida_kg', 'diferencia_porcentaje', 'diferencia_kg',
                    'peso_origen_total', 'peso_destino_total')
    def _onchange_merma_cobrar_kg(self):
        if self.peso_origen_total > self.peso_destino_total:
            if self.excedente_merma:
                if self.excedente_merma == 'No cobrar':
                    self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Porcentaje: Cobrar diferencia':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = (self.merma_kg / 1000) - self.merma_permitida_kg
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                    else:
                        self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Porcentaje: Cobrar todo':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = (self.merma_kg / 1000)
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                    else:
                        self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Kg: Cobrar diferencia':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = (self.merma_kg / 1000) - self.cliente_id.merma_permitida_kg
                        self.merma_permitida_kg = self.cliente_id.merma_permitida_kg
                    else:
                        self.merma_cobrar_kg = 0
                        self.merma_permitida_kg = self.cliente_id.merma_permitida_kg
                if self.excedente_merma == 'Kg: Cobrar todo':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = (self.merma_kg / 1000)
                        self.merma_permitida_kg = self.cliente_id.merma_permitida_kg
                    else:
                        self.merma_cobrar_kg = 0
                        self.merma_permitida_kg = self.cliente_id.merma_permitida_kg
                if self.excedente_merma == 'Cobrar todo':
                    self.merma_cobrar_kg = (self.merma_kg / 1000)
                    self.merma_permitida_kg = self.cliente_id.merma_permitida_kg
        else:
            self.merma_cobrar_kg = 0
            self.merma_permitida_kg = self.cliente_id.merma_permitida_kg


    
    @api.depends('peso_origen_total', 'peso_destino_total', 'merma_kg', 'merma_permitida_kg', 'diferencia_porcentaje',
                    'diferencia_kg')
    def _compute_merma_cobrar_kg(self):
        if self.peso_origen_total > self.peso_destino_total:
            if self.excedente_merma:
                if self.excedente_merma == 'No cobrar':
                    self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Porcentaje: Cobrar diferencia':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = self.merma_kg - self.merma_permitida_kg
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                    else:
                        self.merma_cobrar_kg = 0
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                if self.excedente_merma == 'Porcentaje: Cobrar todo':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = self.merma_kg
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                    else:
                        self.merma_cobrar_kg = 0
                        self.merma_permitida_kg = (self.peso_origen_total * self.cliente_id.merma_permitida_por) / 100
                if self.excedente_merma == 'Kg: Cobrar diferencia':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = self.merma_kg - self.cliente_id.merma_permitida_kg
                    else:
                        self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Kg: Cobrar todo':
                    if self.merma_kg > self.cliente_id.merma_permitida_kg:
                        self.merma_cobrar_kg = self.merma_kg
                    else:
                        self.merma_cobrar_kg = 0
                if self.excedente_merma == 'Cobrar todo':
                    self.merma_cobrar_kg = self.merma_kg
        else:
            self.merma_cobrar_kg = 0

    merma_cobrar_kg = fields.Float(string='Merma cobrar kg', compute='_compute_merma_cobrar_kg', readonly=True)

    @api.onchange('merma_cobrar_kg', 'costo_producto')
    def _onchange_merma_cobrar_pesos(self):
        if self.merma_cobrar_kg > 0:
            self.merma_cobrar_pesos = (self.merma_cobrar_kg) * self.costo_producto
        else:
            self.merma_cobrar_pesos = 0

    
    @api.depends('merma_cobrar_kg', 'costo_producto')
    def _compute_merma_cobrar_pesos(self):
        if self.merma_cobrar_kg > 0:
            self.merma_cobrar_pesos = (self.merma_cobrar_kg) * self.costo_producto
            # self.merma_cobrar_pesos = merma_cobrar_pesos
            valores = {'viaje_id': self.id, 'monto': self.merma_cobrar_pesos, 'tipo_cargo': 'merma',
                        'asociado_id': self.asociado_id.id}
            obc_cargos = self.env['trafitec.cargos'].search(
                ['&', ('viaje_id', '=', self.id), ('tipo_cargo', '=', 'merma')])
            if len(obc_cargos) == 0:
                self.env['trafitec.cargos'].create(valores)
            else:
                obc_cargos.write(valores)
        else:
            self.merma_cobrar_pesos = 0

    merma_cobrar_pesos = fields.Float(string='Merma cobrar $', compute='_compute_merma_cobrar_pesos', readonly=True)

    # Relaciones
    boletas_id = fields.One2many(comodel_name="trafitec.viajes.boletas", inverse_name="linea_id",
                                track_visibility='onchange')
    evidencia_id = fields.One2many(string="Evidencias", comodel_name="trafitec.viajes.evidencias", inverse_name="linea_id",
                                track_visibility='onchange')

    # @api.constrains('comision_calculada')
    # def _datos_correctos(self):
    # Validar la comision
    #    if self.comision_calculada>10000:
    #        raise UserError(_('Alerta..\nEl calculo de comisión es muy grande:'+self.comision_calculada))

    @api.constrains('evidencia_id', 'documentacion_completa', 'name')
    def _check_evidencia(self):
        if self.documentacion_completa == True:
            obj_eviden = self.env['trafitec.viajes.evidencias'].search(
                ['&', ('linea_id', '=', self.id), ('name', '=', 'Evidencia de viaje')])
            if len(obj_eviden) == 0:
                raise UserError(
                    _('Aviso !\nNo puede aplicar como documentación completa, si no tiene ninguna evidencia de viaje'))

    @api.constrains('regla_comision', 'motivo', 'porcent_comision', 'cant_especifica')
    def _check_comision_motivo(self):
        if self.regla_comision == 'No cobrar':
            if self.motivo == False:
                raise UserError(
                    _('Aviso !\nDebe capturar el motivo por el cual no se cobra comisión'))
        if 'Con % especifico' in self.regla_comision:
            if self.porcent_comision == 0 or self.porcent_comision == 0.00:
                raise UserError(
                    _('Aviso !\nDebe capturar el porcentaje de la comisión'))
        if self.regla_comision == 'Cobrar cantidad especifica':
            if self.cant_especifica == 0 or self.cant_especifica == 0.00:
                raise UserError(
                    _('Aviso !\nDebe capturar la cantidad especifica'))

    @api.depends('peso_origen_remolque_1')
    @api.onchange('peso_origen_remolque_1')
    def YOUR_onchange(self):
        res = {'value': {}}
        if not self.peso_origen_remolque_1:
            return res

            # if self.peso_origen_remolque_1 >= 10000:
            # res['value']['peso_origen_remolque_1'] = '123'
            # res['warning'] = {'title': 'Alerta', 'messagge': 'Esta es una alerta personalizada'}
            # return {'warning':{'title':_('Alerta'),'message':_('Esta es una alerta.')}}

        return res

    
    def _compute_conteo(self):
        #viaje = self.env['trafitec.viajes'].search([])
        return 0

    conteo = fields.Char(string="Conteo", compute="_compute_conteo",default="0")
    

    def Valida(self, tipo=1, vals=None):
        #tipo: 1=Create,2=Write,3=Unlink
        #if vals:
        #    origen_destino = self.env['trafitec.cotizaciones.linea.origen'].search([('id', '=', vals['subpedido_id'])])
        #    print("********************Origen destino********************")
        #    print(origen_destino)
        #    evidencias=self.env['trafitec.cotizaciones.evidencias'].search([('id','=',origen_destino.linea_id.cotizacion_id.id)])
        #    if len(evidencias) <= 0:
        #        raise UserError(_("La cotización seleccionda no tiene evidencias de viaje."))
        #    return
        
        if tipo == 1:
            print("-----------------Al agregar")
        elif tipo == 2:
            print("-----------------Al modificar")
        elif tipo == 3:
            print("-----------------Al borrar")
            
        #raise UserError(_(""))
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('trafitec.viajes') or _('New')
        cliente_obj = None
        cliente_dat = None
        error = False
        errores = ""
        
        self.Valida(1, vals)
        
        if self._context.get('validar_credito_cliente', True):
            self._valida_credito(vals, 1)

        if self._context.get('validar_cliente_moroso', True):
            self._valida_moroso(vals)

        #try:
        
        cliente_obj = self.env['res.partner']
        cliente_dat = cliente_obj.browse([vals.get('cliente_id')])
        if cliente_dat:
            if cliente_dat.bloqueado_cliente_bloqueado:
                raise UserError(_('El cliente esta bloqueado, motivo: '+(cliente_dat.bloqueado_cliente_clasificacion_id.name or '')))
        
        #except:
        #    print("Error al validar cliente bloqueado.")
    
        #trafitec.viajes->tipo_remolque (trafitec.moviles)
        #trafitec.viajes->tipo_remolque->capacidad (trafitec.moviles)
        #trafitec.viajes->capacidad (trafitec.moviles)
        #trafitec.viajes->tipo full, sencillo
        
        error = False
        errores = ""
  
        #--------------------------------
        # VEHICULO
        #--------------------------------
        placas_id = self.env['fleet.vehicle'].search([('id', '=', vals['placas_id'])])
        vals['asociado_id'] = placas_id.asociado_id.id
        vals['porcentaje_comision'] = placas_id.asociado_id.porcentaje_comision
        vals['usar_porcentaje'] = placas_id.asociado_id.usar_porcentaje
        vals['creditocomision'] = placas_id.asociado_id.creditocomision
        vals['operador_id'] = placas_id.operador_id.id
        vals['no_economico'] = placas_id.no_economico
        marca = placas_id.name
        
        #ACTUALIZAR EL ESTADO DE FLOTILLA
        if placas_id.es_flotilla:
            vals.update(
                {
                    'estado_viaje': 'iniciado',
                    'slitrack_proveedor': 'geotab',
                    'slitrack_estado': 'iniciado'
                }
            )
            
            viajes_dat = self.env['trafitec.viajes'].search([('placas_id', '=', placas_id.id), ('estado_viaje', '=', 'iniciado')])
            print("-----------------------VIAJES ENCONTRADOS:"+str(viajes_dat))
            for v in viajes_dat:
                v.with_context(validar_credito_cliente=False).write(
                    {
                        'estado_viaje': 'terminado',
                        'slitrack_estado': 'terminado'
                    }
                )
        
        if placas_id.modelo:
            modelo = placas_id.modelo
        else:
            modelo = ''

        if placas_id.color:
            color = placas_id.color
        else:
            color = ''

        str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
        vals['vehiculo'] = str_vehiculo
        #-------------------------------
        # FOLIO
        #-------------------------------

        if 'tipo_remolque' in vals:
            tipo_remol = self.env['trafitec.moviles'].search([('id', '=', vals['tipo_remolque'])])

            if vals['lineanegocio'] == 3 or vals['lineanegocio'] == 2:  # Contenedores o Flete.
                vals['peso_origen_total'] = 1000
                vals['peso_destino_total'] = 1000
                vals['peso_convenido_total'] = 1000
        
                if tipo_remol.tipo == 'sencillo':
                    vals['peso_origen_remolque_1'] = 1000
                    vals['peso_origen_remolque_2'] = 0
                    
                    vals['peso_destino_remolque_1'] = 1000
                    vals['peso_destino_remolque_2'] = 0
                    
                    vals['peso_convenido_remolque_1'] = 1000
                    vals['peso_convenido_remolque_2'] = 0
                    
                else:
                    vals['peso_origen_remolque_1'] = 500
                    vals['peso_origen_remolque_2'] = 500
                    vals['peso_destino_remolque_1'] = 500
                    vals['peso_destino_remolque_2'] = 500
                    vals['peso_convenido_remolque_1'] = 500
                    vals['peso_convenido_remolque_2'] = 500
                




        viaje_nuevo = super(trafitec_viajes, self).create(vals)
        """
        try:
            if 'asignadoa_id' in vals:
                self.env['trafitec.asignaciones'].create({'asignadoa_id' : vals['asignadoa_id'], 'viaje_id': viaje_nuevo.id,'tipo' : 'alcrear'})
        except:
            print('**Error al registrar la asignación al crear el viaje.')
        """
        return viaje_nuevo

    def write(self, vals):
        #if self._context.get('omitir_write', False):
        #    return super(trafitec_viajes, self).write(vals)
        
        self.Valida(2, vals)
        if self._context.get('validar_credito_cliente', True):
            self._valida_credito(vals, 2)
            
        
        error_titulo = "Hay descuentos con abonos:"
        error = False
        errores = ""

        
        if 'asociado_id' in vals:
            descuentos_obj = self.env['trafitec.descuentos']
            descuentos_dat = descuentos_obj.search([('viaje_id', '=', self.id)])
            for d in descuentos_dat:
                if d.abono_total > 0:
                    error = True
                    errores += "Descuento {} total: {:20,.2f}\n".format(d.id, d.monto)
            
            if not error:
                for d in descuentos_dat:
                    d.asociado_id = vals['asociado_id']

        if error:
            raise UserError(_(error_titulo+"\n"+errores))
        
        
        
        if 'placas_id' in vals:
            placas_id = self.env['fleet.vehicle'].search([('id', '=', vals['placas_id'])])
            vals['asociado_id'] = placas_id.asociado_id.id
            vals['porcentaje_comision'] = placas_id.asociado_id.porcentaje_comision
            vals['usar_porcentaje'] = placas_id.asociado_id.usar_porcentaje
            vals['creditocomision'] = placas_id.asociado_id.creditocomision
            vals['operador_id'] = placas_id.operador_id.id
            vals['no_economico'] = placas_id.no_economico
            marca = placas_id.name
            if placas_id.modelo:
                modelo = placas_id.modelo
            else:
                modelo = ''
            if placas_id.color:
                color = placas_id.color
            else:
                color = ''
            str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
            vals['vehiculo'] = str_vehiculo

        if 'tipo_remolque' in vals:
            tipo_remolque = vals['tipo_remolque']
        else:
            tipo_remolque = self.tipo_remolque.id

        #tipo_remol = self.env['trafitec.moviles'].search([('id', '=', tipo_remolque)])
        #if 'Contenedor' in tipo_remol.name:
        #    if tipo_remol.tipo == 'sencillo':
        #        vals['peso_origen_remolque_1'] = 1000
        #        vals['peso_destino_remolque_1'] = 1000
        #    else:
        #        vals['peso_origen_remolque_1'] = 500
        #        vals['peso_origen_remolque_2'] = 500
        #        vals['peso_destino_remolque_1'] = 500
        #        vals['peso_destino_remolque_2'] = 500
        
        # Registrar en bitacora la asignacion.
        
        """
        try:
            if 'asignadoa_id' in vals:
                self.env['trafitec.asignaciones'].create({'asignadoa_id': vals['asignadoa_id'],'viaje_id': self.id,'tipo':'almodificar'})
        except:
            print('**Error al registrar la asignación al modificar el viaje.')
        """
            
        return super(trafitec_viajes, self).write(vals)

    def copy(self):
        raise UserError(_('Alerta..\nNo esta permitido duplicar viajes.'))


    def _valida_moroso(self, vals = None):
        if vals is None:
            return
        
        persona_id = 'cliente_id' in vals and vals['cliente_id'] or self.cliente_id.id
        
        # ---------------------------------
        # OBJETOS
        # ---------------------------------
        saldo = 0.00
        es_moroso = False
        
        persona_obj = self.env['res.partner']
        saldo = persona_obj.saldo_vencido(persona_id)
        es_moroso = persona_obj.es_moroso(persona_id)
        
        if es_moroso:
            raise UserError(_("El cliente tiene facturas vencidas por: {:20,.2f}.".format(saldo)))

    def _valida_credito(self, vals, tipo=1):
        if not self._context.get('validar_credito_cliente', True):
            return
            
        #tipo: 1=Al crear, 2= Al modificar, 3=Al borrar.
        error = False
        errores = ""
        viaje_obj = self.env['trafitec.viajes']
        
        
        #---------------------------------
        # VALORES
        #---------------------------------
        persona_id = 'cliente_id' in vals and vals['cliente_id'] or self.cliente_id.id
        tiporemolque_id = 'tipo_remolque' in vals and vals['tipo_remolque'] or self.tipo_remolque.id
        peso_origen_remolque_1 = 'peso_origen_remolque_1' in vals and vals['peso_origen_remolque_1'] or self.peso_origen_remolque_1
        peso_origen_remolque_2 = 'peso_origen_remolque_2' in vals and vals['peso_origen_remolque_2'] or self.peso_origen_remolque_2
        tarifa_cliente = 'tarifa_cliente' in vals and vals['tarifa_cliente'] or self.tarifa_cliente
        peso_autorizado = 'peso_autorizado' in vals and vals['peso_autorizado'] or self.peso_autorizado

        #---------------------------------
        # OBJETOS
        #---------------------------------
        persona_obj = self.env['res.partner']
        tiporemolque_obj = self.env['trafitec.moviles']
        
        #---------------------------------
        # TIPO DE REMOLQUE DEL VIAJE ACTUAL
        #---------------------------------
        tiporemolque_dat = tiporemolque_obj.search([('id', '=', tiporemolque_id)])
        #capacidad = tiporemolque_dat.capacidad
        capacidad = peso_autorizado
        flete_cliente = tarifa_cliente * (peso_origen_remolque_1 + peso_origen_remolque_2) / 1000
        
        
        if flete_cliente <= 0:
            flete_cliente = tarifa_cliente * (capacidad / 1000)
            print("***FLETE CLIENTE***")
            print(flete_cliente)

        #--------------------------------
        # CLIENTE
        #--------------------------------
        try:
            persona_datos = persona_obj.search([('id', '=', persona_id)])
            cliente_nombre = persona_datos.name
            cliente_saldo = persona_obj.cliente_saldo_total(persona_id, (self.id and self.id or None)) + flete_cliente
            cliente_limite_credito = persona_datos.limite_credito
        
            #print(cliente_nombre, cliente_saldo, cliente_limite_credito)
            #if persona_obj.cliente_saldo_excedido(persona_id, flete_cliente, (self.id and self.id or None)):
            #    error = True
            #    errores = "El cliente {} con saldo {:20,.2f} ha excedido su crédito {:20,.2f} por {:20,.2f}".format(cliente_nombre, cliente_saldo, cliente_limite_credito, cliente_saldo - cliente_limite_credito)
        except:
            print("**Error al evaluar el crédito del cliente al crear el viaje." + str(sys.exc_info()[0] or ""))
            # raise UserError(_("Error al evaluar el crédito del cliente al crear viaje."))

        if error:
            raise UserError(_(errores))

    
    
class trafitec_viajes_boletas(models.Model):
    _name = 'trafitec.viajes.boletas'

    name = fields.Char(string='Folio de boleta', required=True, track_visibility='onchange')
    tipo_boleta = fields.Selection(string="Tipo de boleta", selection=[('Origen', 'Origen'), ('Destino', 'Destino')],
                                    required=True, track_visibility='onchange')
    linea_id = fields.Many2one(comodel_name="trafitec.viajes", string="Folio de viaje", ondelete='cascade')

    fecha = fields.Date(related='linea_id.fecha_viaje', string='Fecha', store=True)
    cliente = fields.Many2one(related='linea_id.cliente_id', string='Cliente', store=True)
    origen = fields.Many2one(related='linea_id.origen', string='Origen', store=True)
    destino = fields.Many2one(related='linea_id.destino', string='Destino', store=True)
    tipo_viaje = fields.Selection(related='linea_id.tipo_viaje', string='Tipo de viaje', store=True)
    factura_id = fields.Many2one(related='linea_id.factura_cliente_id', string='Factura cliente', store=True)
    state = fields.Selection(related='linea_id.state', string='Estado', store=True)

    @api.model
    def create(self, vals):
        object_boletas = self.env['trafitec.viajes.boletas'].search([('name', '=ilike', vals['name'])])
        object_viaje = self.env['trafitec.viajes'].search([('id', '=', vals['linea_id'])])

        for object_bolets in object_boletas:
            if vals['tipo_boleta'] == 'Origen':
                if object_viaje.origen.id == object_bolets.linea_id.origen.id and object_viaje.cliente_id.id == object_bolets.linea_id.cliente_id.id and object_bolets.tipo_boleta == 'Origen':
                    raise UserError(
                        _('Alerta..\nYa existe un folio para este cliente y bodega de origen.'))
            else:
                if object_viaje.destino.id == object_bolets.linea_id.destino.id and object_viaje.cliente_id.id == object_bolets.linea_id.cliente_id.id and object_bolets.tipo_boleta == 'Destino':
                    raise UserError(
                        _('Alerta..\nYa existe un folio para este cliente y bodega de destino.'))

        return super(trafitec_viajes_boletas, self).create(vals)

    
    def write(self, vals):
        if 'name' in vals:
            name = vals['name']
        else:
            name = self.name
        if 'tipo_boleta' in vals:
            tipo_boleta = vals['tipo_boleta']
        else:
            tipo_boleta = self.tipo_boleta
        object_boletas = self.env['trafitec.viajes.boletas'].search([('name', '=ilike', name)])
        object_viaje = self.env['trafitec.viajes'].search([('id', '=', self.linea_id.id)])
        for object_bolets in object_boletas:
            if tipo_boleta == 'Origen':
                if object_viaje.origen.id == object_bolets.linea_id.origen.id and object_viaje.cliente_id.id == object_bolets.linea_id.cliente_id.id and object_bolets.tipo_boleta == 'Origen':
                    raise UserError(
                        _('Aviso !\nYa existe un folio para este cliente y bodega de origen.'))
            else:
                if object_viaje.destino.id == object_bolets.linea_id.destino.id and object_viaje.cliente_id.id == object_bolets.linea_id.cliente_id.id and object_bolets.tipo_boleta == 'Destino':
                    raise UserError(
                        _('Aviso !\nYa existe un folio para este cliente y bodega de destino.'))

        return super(trafitec_viajes_boletas, self).write(vals)


class trafitec_viajes_evidencias(models.Model):
    _name = 'trafitec.viajes.evidencias'

    name = fields.Selection(string="Tipo",
                            selection=[('Evidencia de viaje', 'Evidencia de viaje'), ('Carta porte', 'Carta porte'), ('Carta porte xml', 'Carta porte xml')],
                            required=True, default='Evidencia de viaje')
    image_filename = fields.Char("Nombre del archivo")
    evidencia_file = fields.Binary(string="Archivo", required=True)
    linea_id = fields.Many2one(comodel_name="trafitec.viajes", string="Evidencia id", ondelete='cascade')


class trafitec_viaje_sinestrado(models.TransientModel):
    _name = 'trafitec.viaje.sinestrado.wizard'

    def _get_viajeid(self):
        print(self._context.get('active_id'))
        viajes_obj = self.env['trafitec.viajes'].search([('id', '=', self._context.get('active_id'))])

        if viajes_obj.en_contrarecibo:
            raise UserError(_("El viaje seleccionado ya tiene contra recibo."))

        if viajes_obj.en_factura:
            raise UserError(_("El viaje seleccionado ya tiene factura."))

        if viajes_obj.en_cp:
            raise UserError(_("El viaje seleccionado ya tiene carta porte."))


        return viajes_obj

    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    motivo = fields.Text(string='Motivo de siniestro')

    
    def siniestrado_button(self):
        self.ensure_one()
        for line in self:
            line.viaje_id.write({'motivo_siniestrado': line.motivo, 'state': 'Siniestrado',
                                'fecha_cambio_estado': datetime.datetime.now()})

class trafitec_viaje_cambiartarifa_wizard(models.TransientModel):
    _name = 'trafitec.viaje.cambiartarifa.wizard'

    def _get_viajeid(self):
        print(self._context.get('active_id'))
        viajes_obj = self.env['trafitec.viajes'].search([('id', '=', self._context.get('active_id'))], limit=1)
        return viajes_obj

    def _get_tarifa(self):
        print(self._context.get('active_id'))
        viajes_obj = self.env['trafitec.viajes'].search([('id', '=', self._context.get('active_id'))], limit=1)
        return viajes_obj.tarifa_cliente

    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    tarifa = fields.Float(string='Tarifa', default=_get_tarifa, required=True)

    
    def action_cambiartarifa(self):
        self.ensure_one()
        for line in self:
            #line.viaje_id.with_context(validar_tc=False).write({'tarifa_cliente': line.tarifa})
            line.viaje_id.with_context(validar_tc=True).write({'tarifa_cliente': line.tarifa})


class trafitec_viaje_cancelar(models.TransientModel):
    _name = 'trafitec.viaje.cancelar.wizard'

    def _get_viajeid(self):
        print(self._context.get('active_id'))
        viajes_obj = self.env['trafitec.viajes'].search([('id', '=', self._context.get('active_id'))], limit=1)

        if viajes_obj.en_contrarecibo:
            raise UserError(_("El viaje seleccionado ya tiene contra recibo."))

        if viajes_obj.en_factura:
            raise UserError(_("El viaje seleccionado ya tiene factura."))

        if viajes_obj.en_cp:
            raise UserError(_("El viaje seleccionado ya tiene carta porte."))

        return viajes_obj

    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    motivo = fields.Text(string='Motivo')

    
    def cancelacion_button(self):
        self.ensure_one()
        for line in self:
            if line.viaje_id.state == 'Cancelado':
                raise UserError(_('Aviso !\nNo se puede cancelar un viaje que ya esta cancelado.'))

            if line.viaje_id.en_factura == True:
                raise UserError(_('Aviso !\nNo se puede cancelar un viaje con factura.'))

            if line.viaje_id.en_contrarecibo == True:
                raise UserError(_('Aviso !\nNo se puede cancelar un viaje con contra recibo.'))

            descuento_obj = self.env['trafitec.descuentos'].search([('viaje_id', '=', line.viaje_id.id), ('abono_total', '>' ,0)])
            if len(descuento_obj) > 0:
                raise UserError(_('Aviso !\nNo se puede cancelar un viaje que tenga descuentos relacionados.'))

            comision_obj = self.env['trafitec.cargos'].search(
                [('viaje_id', '=', line.viaje_id.id), ('tipo_cargo', '=', 'comision'), ('abonado', '>', 0)])
            
            if len(comision_obj) > 0:
                raise UserError(_('Aviso !\nNo se puede cancelar un viaje que tenga la comisiones relacionadas.'))

            line.viaje_id.with_context(validar_credito_cliente=False).write({'motivo_cancelacion': line.motivo, 'state': 'Cancelado',
                                    'fecha_cambio_estado': datetime.datetime.now()})


class trafitec_viaje_cargos(models.Model):
    _name = 'trafitec.viaje.cargos'

    name = fields.Many2one('trafitec.tipocargosadicionales', string='Tipos de cargos adicionales', required=True)
    valor = fields.Float(string='Valor', required=True)
    line_cargo_id = fields.Many2one('trafitec.viajes', string='Id viaje')
    sistema = fields.Boolean(string='Sistema', default=False)  # Indica si es un registro del sistema.
    validar_en_cr = fields.Boolean(string='Validar en CR', related='name.validar_en_cr')
    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('pagar_cr_cobrar_f', 'Pagar en contrarecibo y cobrar en factura cliente'),
            ('pagar_cr_nocobrar_f', 'Pagar en contrarecibo y no cobrar en factura cliente'),
            ('nopagar_cr_cobrar_f', 'No pagar en contrarecibo y cobrar en factura cliente')
        ],
        default='pagar_cr_cobrar_f',
        required=True
    )

    @api.constrains('name')
    def _check_name(self):
        obj = self.env['trafitec.viaje.cargos'].search(
            [('name', '=', self.name.id), ('line_cargo_id', '=', self.line_cargo_id.id)])
        """
        if len(obj) > 1:
            raise UserError(
                _('Aviso !\nNo se puede crear cargos del mismo tipo mas de 1 vez.'))
        """

class trafitec_slitrack_registro(models.Model):
    _name = 'trafitec.slitrack.registro'
    _order = 'fechahorag desc'
    viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes')
    fechahorad = fields.Datetime(string='Fecha hora dispositivo')
    fechahorag = fields.Datetime(string='Fecha hora de generación')
    latitud = fields.Float(string='Latitud',default=0, digits=(10,10))
    longitud = fields.Float(string='Longitud',default=0, digits=(10,10))
    velocidad = fields.Float(string='Velocidad',default=0, digits=(10,10))
    detalles = fields.Char(string='Detalles',default='')
    proveedor = fields.Selection(string="Tipo", selection=[('slitrack', 'SLI Track'), ('manual', 'Manual')], default='manual')
    
    @api.model
    def create(self, vals):
        return super(trafitec_slitrack_registro, self).create(vals)
    
    
    def unlink(self):
        for r in self:
            if r.proveedor in ("geotab","slitrack"):
                raise UserError(_("Solo se pueden borrar los registros de tipo manual."))
        return super(trafitec_slitrack_registro, self).unlink()

    @api.constrains
    def _validar(self):
        if not self.create_date:
            raise UserError(_("Debe especificar la fecha y hora."))

        if self.latitud == 0 and self.longitud == 0:
            raise UserError(_("Debe especificar la latitud y longitud."))


    def action_vermapa(self):
        return {
        "type": "ir.actions.act_url",
        "url": "http://maps.google.com/maps?q=loc:"+str(self.latitud)+","+str(self.longitud),
        "target": "blank",
        }
    
class trafitec_asignaciones(models.Model):
    _name = 'trafitec.asignaciones'
    asignadoa_id = fields.Many2one(string='Usuario',comodel_name='res.users',help='Usuario al que se le asigno el viaje.')
    viaje_id = fields.Many2one(string='Viaje',comodel_name='trafitec.viajes',help='Viaje asignado.')
    tipo = fields.Selection(string = 'Tipo',selection=[('alcrear','Al crear'),('almodificar','Al modificar')],default='alcrear')