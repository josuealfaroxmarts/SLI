## -*- coding: utf-8 -*-

from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)


class trafitec_cotizacion(models.Model):
    _name = 'trafitec.cotizacion'
    _description='cotizacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    
    name = fields.Char(string="No. Cotización", copy=False, readonly=True)
    nombre = fields.Char(string="Nombre")
    colonia = fields.Char(string="Colonia")
    estado = fields.Char(string="Estado")
    codigo_postal = fields.Char(string="Código postal")
    ciudad = fields.Char(string="Ciudad")
    presentacion_carga = fields.Selection([('Granel', 'Granel'), ('Costal', 'Costal'), ('Contenedor', 'Contenedor')], string="Presentación de carga")
    lineanegocio = fields.Many2one('trafitec.lineanegocio', string='Linea de negocios', tracking=True)
    contacto = fields.Char(string='Contacto referenciado', required=False,tracking=True)
    contacto2 = fields.Many2one(string='Contacto',comodel_name='res.partner', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    telefono = fields.Char(string='Teléfono',tracking=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Datetime.now,tracking=True)
    validohasta = fields.Date(string='Válido hasta',tracking=True)
    cliente_refenciado = fields.Char(string='Cliente referenciado',tracking=True)
    cliente = fields.Many2one('res.partner', string='Cliente', domain="[('customer','=',1), ('parent_id', '=', False)]",tracking=True)
    direccion = fields.Many2one('res.partner', string='Dirección', domain="['|',('parent_id', '=', cliente),('id','=',cliente)]",tracking=True)
    product = fields.Many2one('product.product', string='Producto',tracking=True)
    producto_referen = fields.Char(string='Producto referenciado',tracking=True)
    #CAMBIOS AL MODULO
    origen_id = fields.Many2one('trafitec.ubicacion', string='Ubicación origen', tracking=True, domain="[('cliente_ubicacion','=',cliente)]")
    destino_id = fields.Many2one('trafitec.ubicacion', string='Ubicación destino', tracking=True, domain="[('cliente_ubicacion','=',cliente)]")
    lavada = fields.Boolean(string="Lavada")
    fumigada = fields.Boolean(string="Fumigada")
    limpia = fields.Boolean(string="Limpia")
    otro = fields.Boolean(string="Otro")
    otro_texto = fields.Char(string="Otro texto")
    camisa = fields.Selection([("false", "No aplica"), ("corta", "Manga corta"), ("larga", "Manga Larga")], default='false')
    tipo_camion =  fields.One2many('trafitec.type_truck', 'tipo_camion')
    material_especial = fields.Char(string="Material Especial")
    chaleco = fields.Selection([("No", "No"), ("Si", "Si")])
    color_chaleco = fields.Char(string='Color del chaleco')
    calzado = fields.Selection([("No", "No"), ("Si", "Si")])
    lentes_seguridad = fields.Boolean(string="Lentes de seguridad")
    casco = fields.Boolean(string="Casco")
    cubre_bocas = fields.Boolean(string="Cubre bocas")
    otro_operador = fields.Char(string="Otro operador")
    sua = fields.Selection([("No", "No"), ("Si", "Si")])
    currency_id = fields.Many2one("res.currency", string="Moneda")
    factor_seguro = fields.Float(string="Factor de seguro", digits=(16, 3), default=0.004)
    #FIN CAMBIOS AL MODULO
    payment_term_id = fields.Many2one('account.payment.term', string='Plazos de pago')
    pay_method_id = fields.Many2one('pay.method', string='Metodo de pago')
    aplicanorma = fields.Boolean(string='Aplica norma SCT-012 por peso medido')
    seguro_mercancia = fields.Boolean(string='Seguro de mercancia',tracking=True, store=True)
    polizas_seguro = fields.Many2one('trafitec.polizas', string='Póliza de seguro',tracking=True)
    porcen_seguro = fields.Float(string='Porcentaje de seguro',tracking=True)
    seguro_entarifa = fields.Boolean(string='Seguro en tarifa', tracking=True, help='El seguro va incluido en la tarifa.')
    costo_producto = fields.Float(string='Costo del producto', required=True,tracking=True)
    reglas_merma = fields.Selection(
        [('No cobrar', 'No cobrar'), ('Porcentaje: Cobrar diferencia', '% Cobrar diferencia'),
        ('Porcentaje: Cobrar todo', '% Cobrar Todo'), ('Kg: Cobrar diferencia', 'Kilogramos cobrar diferencia'),
        ('Kg: Cobrar todo', 'Kilogramos cobrar todo'), ('Cobrar todo', 'Cobrar Todo')], string='Reglas de merma')
    lista_precio = fields.Many2one('product.pricelist', string='Lista de precios', tracking=True)

    iva = fields.Many2one('account.tax', string='IVAS')
    state = fields.Selection([('Nueva', 'Nueva'), ('Autorizada', 'Autorizada'), ('Enviada', 'Enviada'),
                            ('Disponible', 'Disponible'), ('EnEspera', 'En espera'), ('Cancelada', 'Cancelada'), ('Cerrada', 'Cerrada')],
                            string='Estados', default='Nueva', tracking=True)
    lineas_cotizacion_id = fields.One2many('trafitec.cotizaciones.linea', 'cotizacion_id', tracking=True)
    company_id = fields.Many2one('res.company', 'Company',
                                default=lambda self: self.env['res.company']._company_default_get(
                                    'trafitec.cotizacion'))
    motivo_cancelacion = fields.Text(string='Motivo cancelacion', tracking=True)
    fecha_cancelacion = fields.Datetime(string='Fecha de cancelacion', tracking=True)
    x_folio_trafitecw = fields.Char(string='Folio Trafitec Windows',
                                    help="Folio de la orden de carga en Trafitec para windows.",tracking=True)
    sucursal_id = fields.Many2one('trafitec.sucursal', string='Sucursal', tracking=True)
    evidencia_id = fields.One2many(string="Evidencias", comodel_name="trafitec.cotizaciones.evidencias",
                                    inverse_name="cotizacion_id", tracking=True)

    detalles = fields.Text(string='Detalles', default='', tracking=True)
    
    odoo_cotizacion_id = fields.Many2one(string='Cotización odoo', comodel_name='sale.order')
    
    
    cliente_plazo_pago_id = fields.Many2one(string='Plazo de pagos de cliente', comodel_name='account.payment.term')
    asociado_plazo_pago_id = fields.Many2one(string='Plazo de pagos de asociado', comodel_name='account.payment.term')
    
    
    semaforo_valor = fields.Selection(string='Semáforo', selection=[('verde', 'Verde'), ('amarillo', 'Amarillo'), ('rojo', 'Rojo')], default='verde', tracking=True)
    mostrar_en_crm_trafico = fields.Boolean(string='Mostrar en CRM Tráfico', help='Indica si la cotización se mostrara en el CRM Tráfico.', default=False)

    documentos_id = fields.One2many(string='Documentos requeridos', comodel_name='trafitec.cotizaciones.documentos', inverse_name='cotizacion_id', help='Documentos requeridos.')
    
    cliente_bloqueado = fields.Boolean(string='Cliente bloqueado', related='cliente.bloqueado_cliente_bloqueado', store=True, default=False, help='Indica si el cliente esta bloqueado.')
    folio = fields.Char(string="Folio", required=True, copy=False, readonly=True,
                    index=True, default=lambda self: _('New'))
    
    def action_enviarcorreo_autorizacion(self):
        asunto = "Cotización por autorizar: "+str(self.name or "")
        de = (self.env.user.login or '')
        para = self.create_uid.login
        contenido = ""
    
        empleado = None
        jefe = None
        cliente = None
    
        empleado = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        
        if empleado:
            jefe = empleado.parent_id
        
        if jefe:
            para = (jefe.work_email or '')
        
        cliente = (self.cliente.name or self.cliente_refenciado or "")
        
        contenido = 'Estimado '+str(jefe.name or '')+' el usuario '+str(empleado.name or '')+' solicita la autorización de la cotización con folio: '+str(self.name or '')+' para el cliente: '+str(cliente or '')+' Odoo: http://odoo.sli.mx.'
    
        action_ctx = dict(self.env.context)
        view_id = self.env.ref('mail.view_mail_form').id
        return {
            'name': _('Autorizar cotización'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.mail',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            #'res_id': self.ids[0],
            'context': {
                'default_subject': asunto,
                'default_email_from': de,
                'default_email_to': para,
                'default_body_html': contenido,
                'subject': asunto
            }
        }

    @api.onchange('contacto2')
    def onchange_contacto2(self):
        self.email = self.contacto2.email
        self.telefono = self.contacto2.phone or self.contacto2.mobile

    @api.onchange('semaforo_valor')
    def onchange_semaforo_valor(self):
        if self.semaforo_valor:
            if self.semaforo_valor == "rojo":

    def action_enviar_info_cliente(self):
        contenido = ""
        para = ""
        para2 = ""
        contenido += ""
        
        sql = ""
        lista = []
        
        sql = """
        select
ct.name folio,
cl.name folio_cliente,
clo.origen origen_id,
ori.name origen_nombre,
clo.destino destino_id,
des.name destino_nombre,
clo.cantidad cantidad,
coalesce(
(
select
sum(v.peso_origen_total/1000)
from trafitec_viajes as v
where v.subpedido_id = clo.id and v.state = 'Nueva'
)
,0) peso_origen_tons
from trafitec_cotizaciones_linea_origen as clo
    inner join trafitec_cotizaciones_linea as cl on(clo.linea_id=cl.id)
    inner join trafitec_cotizacion as ct on(cl.cotizacion_id=ct.id)
    inner join trafitec_ubicacion as ori on(clo.origen=ori.id)
    inner join trafitec_ubicacion as des on(clo.destino=des.id)
where clo.state='Disponible' and ct.id={} --and ct.name='CO001042'
order by des.name
        """.format(self.id)
        
        self.env.cr.execute(sql)
        lista = self.env.cr.dictfetchall()
        
        glo = self.env['trafitec.glo']
    
        if not self.contacto and not self.contacto2:
            raise UserError(_("La cotización no tiene especificado el contacto."))
    
        if not self.email:
            raise UserError(_("La cotización no tiene especificado el correo del contacto."))
        else:
            if not '@' in self.email:
                raise UserError(_("El correo del contacto es incorrecto: " + str(self.email or "")))
    
        estilo_noborde = "border-style: none; border-color:silver; border-width:0px;"
        estilo_borde = "border-style: dotted; border-color:silver; border-width:1px; padding:5px;"
        estilo_borde_redondo = "border-style: none; border-color:none; brder-width:0px; padding:5px; border-radius:10px;"
        estilo_fondo_cabecera = "background-color: red; color:white;"
        estilo_fondo_subtotal = "background-color: #cccccc; color:black;" + estilo_borde_redondo
        estilo_texto = "font-size: 12px; text-align:right; font-family:arial;"
        estilo_texto_negritas = estilo_texto + "font-weight: bold;"
        estilo_etiqueta = estilo_texto + "font-weight: bold;"
        
        estilo = "font-size: 12px; text-align:right; font-family:arial; font-weight: bold;" + estilo_fondo_subtotal
        estilo_fondo = "background-color:silver; font-size: 12px; font-family:arial;"+estilo_noborde
        estilo_normal = "font-size: 12px; font-family:arial;"+estilo_borde
        estilo_cabecera = "font-size: 12px; font-family:arial;"+estilo_borde_redondo+estilo_fondo_cabecera
        estilo_normal_origen_destino = "font-size: 10px; font-family:arial;"+estilo_borde
        estilo_moneda_rojo = "font-size: 12px; text-align:right; font-family:arial; color: red;"+estilo_borde
        estilo_moneda_verde = "font-size: 12px; text-align:right; font-family:arial; color: green;"+estilo_borde
        estilo_tons = "font-size: 12px; text-align:right; font-family:arial;"+estilo_borde
        estilo_tons_subtotal = "font-size: 12px; text-align:right; font-family:arial; font-weight: bold;" + estilo_noborde + estilo_fondo_subtotal
        estilo_hr = "border-color:#dddddd; border-style:dotted;"+estilo_borde
    
        lineas_obj = self.env['trafitec.cotizaciones.linea']
        origendestino_obj = self.env['trafitec.cotizaciones.linea.origen']
        viajes_obj = self.env['trafitec.viajes']
    
        lineas_dat = lineas_obj.search([('cotizacion_id', '=', self.id)])
        origendestino_dat = None
        viajes_dat = None
    
        #nueva = sorted(lineas_dat, key=lambda k: k[''])
    
        contenido = ""
        contenido += "<img src='http://sli.mx/media/logo.png'/><br/>"
        contenido += "<b>SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV</b>"
        contenido += "<hr style='{0}'/>".format(estilo_hr)
        contenido += "CLIENTE: " + str(self.cliente.name or self.cliente_refenciado or "") + "<br/>"
        contenido += "PEDIDO: " + str(self.name or "") + "<br/>"
        contenido += "LINEA NEGOCIO: " + str(self.lineanegocio.name or "") + "<br/>"
        contenido += "<hr style='{0}'/>".format(estilo_hr)
        contenido += "Estimado(a) {0} por este medio le hacemos llegar el avance general del pedido con folio {1}.".format((self.contacto or self.contacto2.name), self.name)
        contenido += "<hr style='{0}'/>".format(estilo_hr)
    
        cantidad = 0
    
        contenido += "<table border=0 cellspacing=1>"
        contenido += "<tr>"

        if self.lineanegocio.id == 1: #Granel.
            contenido += "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'>ORIGEN</th><th style='{0}'>DESTINO</th><th style='{0}'>TONS A MOVER</th><th style='{0}'>TONS MOVIDAS</th><th style='{0}'>TONS SALDO</th><th style='{0}'>AVANCE (%)</th>".format(estilo_cabecera)
        elif self.lineanegocio.id == 2: #Flete.
            contenido += "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'>ORIGEN</th><th style='{0}'>DESTINO</th><th style='{0}'>VIAJES A MOVER</th><th style='{0}'>VIAJES REALIZADOS</th><th style='{0}'>VIAJES SALDO</th><th style='{0}'>AVANCE (%)</th>".format(estilo_cabecera)
        else: #Contenedores.
            contenido += "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'>ORIGEN</th><th style='{0}'>DESTINO</th><th style='{0}'>CONTENEDORES A MOVER</th><th style='{0}'>CONTENEDORES MOVIDOS</th><th style='{0}'>CONTENEDORES SALDO</th><th style='{0}'>AVANCE (%)</th>".format(estilo_cabecera)

        contenido += "</tr>"
        cantidad = 0
        avance = 0
        saldo = 0
        
        total_cantidad = 0
        total_peso = 0
        total_saldo = 0
        total_avance = 0
        
        destino_ant_id = -1
        destino_act_id = -1
        
        subtotal_cantidad = 0
        subtotal_peso = 0
        subtotal_saldo = 0
        subtotal_avance = 0
        
        if len(lista) > 0:
            destino_act_id = lista[0].get('destino_id', -1)
            destino_ant_id = lista[0].get('destino_id', -1)
        
        c = 0
        for od in lista:
            c += 1
            peso = 0
            avance = 0
            folio_cliente = ""
            
            #Destino actual.
            destino_act_id = od.get('destino_id', -1)
            
            cantidad = od.get('cantidad', 0)
            peso = od.get('peso_origen_tons', 0)
            folio_cliente = od.get('folio_cliente', "")
            origen = od.get('origen_nombre', "")
            destino = od.get('destino_nombre', "")

            total_cantidad += cantidad
            total_peso += peso

            if destino_act_id != destino_ant_id:
                subtotal_saldo = subtotal_cantidad - subtotal_peso
    
                if subtotal_cantidad > 0:
                    subtotal_avance = subtotal_peso * 100 / subtotal_cantidad
    
                contenido += "<tr>"
                contenido += "<td style='{0}'></td>".format(estilo_noborde)
                contenido += "<td style='{0}'></td>".format(estilo_noborde)
                contenido += "<td style='{0}'>SUBTOTAL</td>".format(estilo_etiqueta + estilo_noborde)
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_cantidad or 0))
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_peso or 0))
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_saldo or 0))
                contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(estilo, (subtotal_avance or 0))
                contenido += "</tr>"
    
                subtotal_cantidad = 0
                subtotal_peso = 0

            subtotal_cantidad += cantidad
            subtotal_peso += peso

            if cantidad > 0:
                avance = peso * 100 / cantidad
        
            saldo = cantidad - peso
            estilo = estilo_moneda_verde
            if avance <= 50:
                estilo = estilo_moneda_rojo
        
            contenido += "<tr>"
            contenido += "<td style='{0}'>{1}</td>".format(estilo_normal, str(folio_cliente or ""))
            contenido += "<td style='{0}'>{1}</td>".format(estilo_normal_origen_destino, str(origen or ""))
            contenido += "<td style='{0}'>{1}</td>".format(estilo_normal_origen_destino, str(destino or ""))
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons, (cantidad or 0))
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons, (peso or 0))
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons, (saldo or 0))
            contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(estilo, (avance or 0))
            contenido += "</tr>"

            if c == len(lista):
                subtotal_saldo = subtotal_cantidad - subtotal_peso
    
                if subtotal_cantidad > 0:
                    subtotal_avance = subtotal_peso * 100 / subtotal_cantidad
    
                contenido += "<tr>"
                contenido += "<td style='{}'></td>".format(estilo_noborde)
                contenido += "<td style='{}'></td>".format(estilo_noborde)
                contenido += "<td style='{}'>SUBTOTAL</td>".format(estilo_etiqueta+estilo_noborde)
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_cantidad or 0))
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_peso or 0))
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (subtotal_saldo or 0))
                contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(estilo, (subtotal_avance or 0))
                contenido += "</tr>"
    
                subtotal_cantidad = 0
                subtotal_peso = 0

            #Destino anterior.
            destino_ant_id = od.get('destino_id', -1)

        #Totales.
        total_saldo = total_cantidad - total_peso
        if total_cantidad > 0:
            total_avance = total_peso * 100 / total_cantidad
        
        contenido += "<tr>"
        contenido += "<td style='{0}'></td>".format(estilo_noborde)
        contenido += "<td style='{0}'></td>".format(estilo_noborde)
        contenido += "<td style='{0}'>TOTAL</td>".format(estilo_etiqueta+estilo_noborde)
        contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (total_cantidad or 0))
        contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (total_peso or 0))
        contenido += "<td style='{0}'>{1:20,.3f}</td>".format(estilo_tons_subtotal, (total_saldo or 0))
        contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(estilo, (total_avance or 0))
        contenido += "</tr>"
        
        contenido += "</table>"

        #Obtiene la configuración.
        cfg = glo.cfg()
        
        #raise UserError(_("CFG: "+str(cfg)))
        para = self.email
        para2 = self.create_uid.login
        if cfg:
            if cfg.cot_envio_avance_pruebas_st and cfg.cot_envio_avance_pruebas_correo:
                para = cfg.cot_envio_avance_pruebas_correo
                para2 = ""
        
        #Enviar al contacto.
        #para += self.cotizacion_id.email
        #Enviar a quien genero la cotizacion.
        #para += self.create_uid.login
        
        #para = "cotizaciones_reportes@sli.mx"
        if ('@' in para) or ('@' in para2):
            self.enviar_correo(asunto="SLI PEDIDO {}".format(self.name), contenido=contenido, para=para, para2=para2)

    def enviar_correo(self, asunto='', contenido='', para='', para2=''):
        valores = {
            'subject': asunto,
            'body_html': contenido,
            'email_to': para,
            'email_cc': para2,
            'email_from': 'info@sli.mx',
        }
        create_and_send_email = self.env['mail.mail'].create(valores).send()

    
    def unlink(self):
        print(dir(self))
        raise UserError(_('Alerta..\nNo esta permitido borrar cotizaciones.'))
        """
        for reg in self:
            if reg.state == 'Disponible' or reg.state == 'Cerrada':
                raise UserError(_(
                    'Aviso !\nNo se puede eliminar si la cotizacion({}) esta disponible o cerrada.'.format(reg.name)))
        return super(trafitec_cotizacion, self).unlink()
        """

    @api.depends('lineas_cotizacion_id.subtotal', 'seguro_mercancia')
    def _monto_total(self):
        for order in self:
            monto = 0
            for line in order.lineas_cotizacion_id:
                if monto == 0:
                    monto = line.subtotal
                else:
                    monto += line.subtotal
                if order.seguro_mercancia == True:
                    seguro_total_mercancia = (order.costo_producto * order.factor_seguro) * (order.lineas_cotizacion_id.cantidad * 1000) 
                    monto += seguro_total_mercancia
            order.update({
                'monto_total': monto
            })

    monto_total = fields.Float(string='Monto Total aproximado', readonly=True, compute=_monto_total, store=True)
    monto_inicial = fields.Float(string='Monto Final', readonly=True, store=True, default=0.00)


    @api.constrains('cliente_refenciado', 'cliente')
    def _check_clientes(self):
        if self.cliente_refenciado == False and self.cliente.name == False:
            raise UserError(
                _('Aviso !\nDebe especificar un cliente referenciado o del catalago de clientes.'))


    @api.constrains('contacto2', 'contacto')
    def _check_contacto(self):
        if self.contacto == False and self.contacto2.name == False:
            raise UserError(
                _('Aviso !\nDebe especificar un contacto referenciado o del catalago de contactos.'))

    
    @api.constrains('producto_referen', 'product')
    def _check_producto(self):
        if self.producto_referen == False and self.product.name == False:
            raise UserError(
                _('Aviso !\nDebe especificar un producto referenciado o del catalago de productos.'))

    
    @api.onchange('product')
    def _onchange_product(self):
        try:
            self.producto_referen = self.product.name
        except:
            print("Cambio el producto")
        
        self.costo_producto = self.product.product_tmpl_id.list_price

    def _valida_moroso(self, vals=None):
        if vals is None:
            return
        
        persona_id = 'cliente' in vals and vals['cliente'] or self.cliente.id
    
        # ---------------------------------
        # OBJETOS
        # ---------------------------------
        saldo = 0.00
        es_moroso = False
    
        persona_obj = self.env['res.partner']
        saldo = persona_obj.saldo_vencido(persona_id)
        es_moroso = persona_obj.es_moroso(persona_id)
    
        if es_moroso:
            raise UserError(_("El cliente tiene facturas vencidas por: {0:.2f}.".format(saldo)))


    @api.model
    def create(self, vals):
        #----------------------------------------------------
        #Validaciones
        #----------------------------------------------------
        #if self._context.get('validar_cliente_moroso', True):
        #    self._valida_moroso(vals)
        # ----------------------------------------------------

        # raise UserError(str(self._context))
        if vals.get('folio', _('New')) == _('New'):
            vals['folio'] = self.env['ir.sequence'].next_by_code('trafitec.cotizacion') or _('New')
        
        if 'cliente' in vals:
            cliente_obj = self.env['res.partner']
            cliente_dat = cliente_obj.browse([vals.get('cliente')])
            if cliente_dat:
                if cliente_dat.bloqueado_cliente_bloqueado:
                    raise UserError(_('El cliente esta bloqueado, motivo: ' + (cliente_dat.bloqueado_cliente_clasificacion_id.name or '')))
        

        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Cotizacion') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Cotizacion') or _('Nuevo')
        vals['state'] = 'Nueva'


        #linea_nego_obj = self.env['trafitec.lineanegocio'].search([('id', '=', vals['lineanegocio'])])
        #print("************lineax self: " + str(linea_nego_obj))

        #if linea_nego_obj.name == 'Granel' or linea_nego_obj.name == 'GRANEL' or linea_nego_obj.name == 'granel':
        #    if not 'reglas_merma' in vals:
        #        raise UserError(
        #            _('Aviso !\nDebe seleccionar una regla de merma para granel.'))
            
            
        nuevo = super(trafitec_cotizacion, self).create(vals)
        return nuevo
    
    @api.model
    def genera_pedido_venta(self):
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        cliente_obj = self.env['res.partner']
        cliente_dat = cliente_obj.browse([self.cliente.id])
        trafitec_cfg_obj = self.env['trafitec.parametros']
        trafitec_cfg_dat = trafitec_cfg_obj.search([('company_id', '=', self.env.user.company_id.id)])
    
        #Si no esta especificado el producto termina.
        if not trafitec_cfg_dat.cot_producto_id:
            return
        
        valores = {
            'partner_id': self.cliente.id,
            'origin': 'Cotización trafitec: ' + (self.name or ''),
            'client_order_ref': '',
            'state': 'draft',  # 'validity_date': self.
            'note': '',
            'product_id': trafitec_cfg_dat.cot_producto_id.id,
            'trafitec_cotizacion_id': self.id,
            'payment_term_id': self.payment_term_id.id,
            'team_id': cliente_dat.equipoventa_id.id
        }
        print("---NUEVO SALE ORDER---")
        print(valores)
        sale_order_nuevo = sale_order_obj.create(valores)
    
        valores = {
            'order_id': sale_order_nuevo.id,
            'order_partner_id': self.cliente.id,
            'product_id': trafitec_cfg_dat.cot_producto_id.id,
            'product_uom_qty': 1,
            'product_uom': trafitec_cfg_dat.cot_producto_id.product_tmpl_id.uom_id.id,
            'price_unit': self.monto_total,
            'name': (sale_order_nuevo.name or '')
        }
        print("---NUEVO SALE ORDER LINE---")
        print(valores)
        # sale_order_nuevo = sale_order_obj.create(valores)
        sale_order_line_obj.create(valores)
        sale_order_nuevo.action_confirm()
        
        self.odoo_cotizacion_id = sale_order_nuevo.id

    
    def write(self, vals):
        for data in self :
            #print("********self write: " + str(self))
            #print("********vals write: " + str(vals))
            if 'lineanegocio' in vals:
                linea_nego_id = vals['lineanegocio']
            else:
                linea_nego_id = data.lineanegocio.id
            if 'reglas_merma' in vals:
                regla_mer = vals['reglas_merma']
            else:
                regla_mer = data.reglas_merma
            linea_nego_obj = data.env['trafitec.lineanegocio'].search([('id', '=', linea_nego_id)])
            print("********LINEANEGOCIO: "+str(linea_nego_obj))
            
            #if linea_nego_obj.name == 'Granel' or linea_nego_obj.name == 'GRANEL' or linea_nego_obj.name == 'granel':
            #    if regla_mer == False:
            #        raise UserError(
            #            _('Aviso !\nDebe seleccionar una regla de merma para granel.'))
                
                
            if 'semaforo_valor' in vals:
                if vals['semaforo_valor'] == 'rojo':
                    correo = ''
                    
                    try:
                        usuario = data.create_uid
                        empleado = data.env['hr.employee'].search([('user_id', '=', usuario.id)])
                    
                        correo = empleado.parent_id.work_email
                        print("----CORREO----")
                        print(correo)
                    except:
                        print("**No hay correo.")
                    
                    if correo != '':
                        mensaje = ''
                        mensaje += 'Cotización: {}<br/>'.format(data.name or '')
                        mensaje += 'Cliente: {}<br/>'.format(data.cliente.name or '')
                        mensaje += 'Producto: {}<br/>'.format(data.product.name or '')
                        glo = data.env['trafitec.glo']
                        glo.enviar_correo(correo, "Cotización en Rojo", mensaje)
                    
            return super(trafitec_cotizacion, data).write(vals)

    @api.onchange('cliente')
    def _onchange_cliente(self):
        try:
            self.cliente_refenciado = self.cliente.name
        except:
            print("Cambio el cliente")
        
        if self.cliente:
            #Documentos requeridos obtenidos del cliente.
            losdocs = []
            documentos_cliente = self.env['trafitec.clientes.documentos'].search([('partner_id', '=', self.cliente.id), '|', ('name.evidencia', '=', True), ('name.dmc', '=', True)])
            for d in documentos_cliente:
                losdocs.append({'tipodocumento_id': d.name})
                
            self.documentos_id = losdocs
            
            if not self.payment_term_id:
                self.payment_term_id = self.cliente.property_payment_term_id.id
            if not self.pay_method_id:
                self.pay_method_id = self.cliente.pay_method_id.id
            self.direccion = self.cliente
            self.reglas_merma = self.cliente.excedente_merma
            return {
                'domain': {
                    'domicilio': ['|', ('parent_id', '=', self.cliente.id), ('id', '=', self.cliente.id)]
                }
            }

    @api.onchange('polizas_seguro')
    def _onchange_porcentaje(self):
        if self.polizas_seguro:
            self.porcen_seguro = self.polizas_seguro.porcentaje_clie

    
    def action_authorized(self):
        if len(self.lineas_cotizacion_id) == 0:
            raise UserError(
                _('Error !\nTiene que tener lineas antes de poder autorizar esta cotizacion.'))
        else:
            self.write({'state': 'Autorizada'})

    
    def action_reactivate(self):
        self.write({'state': 'Nueva'})

    
    def action_send(self):
        if len(self.lineas_cotizacion_id) == 0:
            raise UserError(
                _('Error !\nTiene que tener lineas antes de poder enviar esta cotizacion.'))
        else:
            self.write({'state': 'Enviada'})

    
    def action_accepted(self):
        if len(self.lineas_cotizacion_id) == 0:
            raise UserError(_('Error !\nTiene que tener lineas antes de poder aceptar esta cotización.'))
        
        self.write({'state': 'Aceptada'})
        

    
    def action_rejected(self):
        self.write({'state': 'Rechazada'})

    
    def action_close(self):
        self.write({'state': 'Cerrada'})

    
    def action_enespera(self):
        self.write({'state': 'EnEspera'})
    
    
    def action_available(self):
        if self.cliente.name == False:
            raise UserError(
                _('Error !\nTiene que dar de alta el cliente en el catalogo y asignarlo a la cotizacion'))
        if self.product.name == False:
            raise UserError(
                _('Error !\nTiene que dar de alta el producto en el catalogo y asignarlo a la cotizacion'))
        for lineas in self.lineas_cotizacion_id:
            print("ID " + str(lineas.id))
            print("Cantidad origen " + str(len(lineas.origen_id)))
            

        linea_nego_obj = self.env['trafitec.lineanegocio'].search([('id', '=', self.lineanegocio.id)])
        print("************lineax self: " + str(linea_nego_obj))

        if linea_nego_obj.name == 'Granel' or linea_nego_obj.name == 'GRANEL' or linea_nego_obj.name == 'granel':
            if not self.reglas_merma:
                raise UserError(_('Debe seleccionar una regla de merma.'))

        self.genera_pedido_venta()
        
        if len(self.lineas_cotizacion_id) == 0:
            raise UserError(
                _('Error !\nTiene que tener lineas antes de poder asignar esta cotizacion como disponible.'))
        else:
            self.write({'state': 'Disponible'})

class trafitec_type_truck(models.Model):
    _name = 'trafitec.type_truck'
    _description='type truck'

    tipo_camion = fields.Many2one('trafitec.cotizacion', string='Tipo camion')
    type_truck = fields.Selection([("Jaula", "Jaula"), ("Caja seca", "Caja seca"), ("Portacontenedor", "Portacontenedor"), ("Tolva", "Tolva"), ("Plataforma", "Plataforma"), ("Gondola", "Gondola"), ("Torton", "Torton"), ("Rabon", "Rabon"), ("Chasis", "Chasis"), ("Thermo 48", "Thermo 48"), ("Thermo 53", "Thermo 53")], string="Tipo Camion")

#TODO HABLAR CON EL CONSULTOR LINEA 753
""" class trafitec_localidad_municipios_estado_pais(models.Model):
    _inherit = 'res.colonia.zip.sat.code'

    
    @api.depends('name')
    def name_get(self):
        result = []
        name = ""
        for rec in self:
            if rec.name:
                name = '[' + (rec.zip_sat_code.code or "") + '] ' + (rec.name  or "") + '/' + (rec.zip_sat_code.township_sat_code.name or "") + '/' + (rec.zip_sat_code.township_sat_code.state_sat_code.name or "") + '/' + (rec.zip_sat_code.township_sat_code.state_sat_code.country_sat_code.name or "")
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|', '|', ('name', 'ilike', name), ('zip_sat_code.township_sat_code.name', 'ilike', name),
                    ('zip_sat_code.township_sat_code.state_sat_code.name', 'ilike', name),
                    ('zip_sat_code.township_sat_code.state_sat_code.country_sat_code.name', 'ilike', name)]
        result = self.search(domain + args, limit=limit)
        res = result.name_get()
        return res """


""" class trafitec_municipios_estado_pais(models.Model):
    _inherit = 'res.country.township.sat.code'

    
    @api.depends('name')
    def name_get(self):
        result = []
        name=""
        for rec in self:
            if rec.name:
                name = (rec.name or "") + '/' + (rec.state_sat_code.name or "") + '/' + (rec.state_sat_code.country_sat_code.name or "")
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result
 """

class trafitec_cotizacion_line(models.Model):
    _name = 'trafitec.cotizaciones.linea'
    _description='cotizaciones linea'
    name = fields.Char(string='Folio de cliente')
    municipio_origen_id = fields.Char( string='Municipio Origen', required=True)
    municipio_destino_id = fields.Char(string='Municipio Destino', required=True)
    distancia = fields.Float(string='Distancia', required=True)
    km_vacio = fields.Float(string='Km. vacio')
    km_cargado = fields.Float(string='Km. Cargado')
    ritmo_carga = fields.Float(string='Ritmo de carga')

    tarifa_asociado = fields.Float(string='Tarifa asociado', required=True)
    tarifa_cliente = fields.Float(string='Tarifa cliente', required=True)
    cantidad = fields.Integer(string='Cantidad', required=True)
    product_uom = fields.Many2one('uom.uom', string='Unidad de medida', required=True,
                                domain="[('trafitec','=',True)]")
    detalle_asociado = fields.Text(string='Detalle Origen')
    detalle_destino = fields.Text(string='Detalle Destino')
    cotizacion_id = fields.Many2one('trafitec.cotizacion', string='Cotizacion', ondelete='cascade')
    nombre_cotizacion = fields.Char(related='cotizacion_id.nombre', string='Nombre de cotizacion')
    cliente_cotizacion = fields.Many2one(related='cotizacion_id.cliente', string='Cliente')
    origen_ubicacion = fields.Many2one(related='cotizacion_id.origen_id', string='Ubicacion origen')
    destino_ubicacion = fields.Many2one(related='cotizacion_id.destino_id', string='Ubicacion destino')
    cargos_id = fields.One2many('trafitec.cotizaciones.linea.cargos', 'linea_id')
    origen_id = fields.One2many('trafitec.cotizaciones.linea.origen', 'linea_id')
    negociacion_id = fields.One2many('trafitec.cotizacion.linea.negociacion', 'linea_id')
    currency_id = fields.Many2one("res.currency", related='cotizacion_id.lista_precio.currency_id', string="Currency",
                                readonly=True,
                                required=True)
    state = fields.Selection(string='Estado', related='cotizacion_id.state', store=True, readonly=True)
    permitir_ta_mayor_tc = fields.Boolean(string='Ta>tc', default=False, help='Pertimir ta mayor a tc.')

    @api.constrains('negociacion_id')
    def _check_negociaciones(self):
        error = False
        errores = ''

        tiene_asociado = False
        tiene_tiporemolque = False

        #Validar duplicados de asociados y tipo de remolque.
        for n in self.negociacion_id:
            tiene_asociado = False
            tiene_tiporemolque = False

            if n.asociado_id:
                tiene_asociado = True

            if n.tiporemolque_id:
                tiene_tiporemolque = True

            if not tiene_asociado and not tiene_tiporemolque:
                error = True
                errores += 'Debe especificar el asociado o el tipo de remolque en cada negociación.\n'



            if tiene_asociado and tiene_tiporemolque:
                for n2 in self.negociacion_id:
                    if n.id == n2.id or n.asociado_id.id != n2.asociado_id.id:
                        continue

                    if n.tiporemolque_id.id == n2.tiporemolque_id.id:
                        raise UserError("El asociado {} ya tiene registro con tipo de remolque {}".format(n.asociado_id.name, n.tiporemolque_id.name))

        if error:
            raise UserError(errores)

    @api.constrains('cantidad')
    def _check_cantidad(self):
        if self.cantidad <= 0:
            raise UserError(_('Error !\nEn la cantidad debe ser un valor mayor 0'))

    @api.constrains('distancia')
    def _check_distancia(self):
        if self.distancia < 0:
            raise UserError(_('Error !\nNo se permite valores negativos en la distancia'))

    @api.constrains('km_vacio')
    def _check_km_vacio(self):
        if self.km_vacio < 0:
            raise UserError(_('Error !\nNo se permite valores negativos en el Km. Vacio'))

    @api.constrains('km_cargado')
    def _check_km_cargado(self):
        if self.km_cargado < 0:
            raise UserError(_('Error !\nNo se permite valores negativos en el Km. Cargado'))

    @api.constrains('tarifa_asociado')
    def _check_tarifa_asociado(self):
        if self.tarifa_asociado <= 0:
            raise UserError(_('Error !\nNo se permite valores negativos o en 0 en la tarifa asociado'))

    @api.constrains('tarifa_cliente')
    def _check_tarifa_cliente(self):
        if self.tarifa_cliente <= 0:
            raise UserError(_('Error !\nNo se permite valores negativos o en 0 en la tarifa cliente'))

    @api.constrains('ritmo_carga')
    def _check_ritmo_carga(self):
        if self.ritmo_carga < 0:
            raise UserError(_('Error !\nNo se permite valores negativos o en 0 en el ritmo de carga'))

    @api.constrains('tarifa_cliente', 'tarifa_asociado')
    def _check_tarifas_mayor(self):
        if self.tarifa_asociado > self.tarifa_cliente:
            if not self.permitir_ta_mayor_tc:
                raise UserError(_('Error !\nLa tarifa asociado no puede ser mayor a la tarifa cliente.'))

    
    def _total_mov(self):
        print("************self: "+str(self))
        if self.tarifa_cliente and self.cantidad:
            self.total_movimientos = self.cantidad * self.tarifa_cliente
        else:
            self.total_movimientos = 0
        return

    total_movimientos = fields.Monetary(string='Total movimientos', readonly=True, compute='_total_mov',
                                        tracking=True)

    @api.onchange('cantidad')
    def total_mov(self):
        if self.tarifa_cliente and self.cantidad:
            self.total_movimientos = self.cantidad * self.tarifa_cliente

    @api.onchange('tarifa_asociado', 'tarifa_cliente')
    def _onchange_tarifa(self):
        if self.tarifa_cliente > 0 and self.tarifa_asociado > 0:
            if self.tarifa_asociado > self.tarifa_cliente:
                if not self.permitir_ta_mayor_tc:
                    raise UserError(_('Error !\n La tarifa asociado no puede ser mayor a la tarifa cliente.'))

    @api.depends('cargos_id.total')
    def _total_cargos(self):
        for cargos in self:
            monto = 0
            for line in cargos.cargos_id:
                if monto == 0:
                    monto = line.total
                else:
                    monto += line.total
            cargos.update({
                'total_cargos': monto
            })

    total_cargos = fields.Monetary(string='Total cargos', readonly=True, compute='_total_cargos',
                                    tracking=True)

    
    def _subtotal(self):
        self.subtotal = self.total_cargos + self.total_movimientos
        return
    subtotal = fields.Monetary(string='Subtotal', readonly=True, compute='_subtotal', tracking=True)

    
    def explict_subscription(self):
        action_ctx = dict(self.env.context)
        view_id = self.env.ref('sli_trafitec.linea_Cargos_form_inherit').id
        return {
            'name': _('Cargos adicionales'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trafitec.cotizaciones.linea',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }

    
    def explict_origen_dest(self):
        action_ctx = dict(self.env.context)
        action_ctx.update({
            'municipio_origen': self.municipio_origen_id.id,
            'municipio_destino': self.municipio_destino_id.id
        })
        view_id = self.env.ref('sli_trafitec.linea_origenes_form_inherit').id
        return {
            'name': _('Origenes y destinos'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trafitec.cotizaciones.linea',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }

    
    def explict_negociacion(self):
        action_ctx = dict(self.env.context)
        view_id = self.env.ref('sli_trafitec.linea_negociancion_form_inherit').id
        return {
            'name': _('Negociaciones'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'trafitec.cotizaciones.linea',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }


class trafitec_cotizacion_line_cargos(models.Model):
    _name = 'trafitec.cotizaciones.linea.cargos'
    _description='cotizaciones linea cargos'
    name = fields.Many2one('trafitec.tipocargosadicionales', string='Tipos de cargos adicionales', required=True)
    iva = fields.Many2one('account.tax', string='IVAS', required=True)
    tipocalculo = fields.Selection([('Suma', 'Suma'), ('Multiplicado', 'Multiplicado')], string='Tipo de cálculo',
                                    required=True)
    valor = fields.Float(string='Valor', required=True)
    linea_id = fields.Many2one('trafitec.cotizaciones.linea', ondelete='restrict')

    
    def _total_lineas(self):
        #if self.tipocalculo and self.valor:
        #    if self.tipocalculo == 'Suma':
        #        self.total = self.valor
        #    else:
        #        if self.tipocalculo == 'Multiplicado':
        #            self.total = self.valor * self.linea_id.cantidad
	    return
    total = fields.Float(string='Total', readonly=True, compute='_total_lineas')

    @api.constrains('valor')
    def _check_valor(self):
        if self.valor <= 0:
            raise UserError(_('Error !\nEn el valor debe ser un valor mayor 0'))


class trafitec_cotizacion_line_origen(models.Model):
    _name = 'trafitec.cotizaciones.linea.origen'
    _description='cotizaciones linea origen'
    name = fields.Char(string='Folio', readonly=True)
    origen = fields.Many2one('trafitec.ubicacion', string='Ubicación origen', required=True)
    destino = fields.Many2one('trafitec.ubicacion', string='Ubicación destino', required=True)
    cantidad = fields.Float(string='Cantidad', required=True)
    facturar = fields.Boolean(string='Facturar', default=True)
    psf = fields.Boolean(string='PSF')
    csf = fields.Boolean(string='CSF')
    linea_id = fields.Many2one('trafitec.cotizaciones.linea', ondelete='restrict')
    folio_cotizacion = fields.Char(string="No. de cotización", related='linea_id.cotizacion_id.name', readonly=True,
                                    store=True)
    cliente_cotizacion = fields.Many2one('res.partner', related='linea_id.cotizacion_id.cliente', readonly=True,
                                        store=True)
    state = fields.Selection([('Disponible', 'Disponible'), ('EnEspera', 'En espera'), ('Cancelada', 'Cancelada'), ('Cerrada', 'Cerrada')], string='Estado', default='Disponible')


    
    @api.depends('name', 'folio_cotizacion', 'cliente_cotizacion', 'origen', 'destino')
    def name_get(self):
        result = []
        name=""
        for rec in self:
            if rec.name and rec.folio_cotizacion and rec.cliente_cotizacion and rec.origen and rec.destino:
                name = (rec.folio_cotizacion or "") + '/' + (rec.name or "") + '/' + (rec.cliente_cotizacion.name or "") + '/' + (rec.origen.name or "") + '/' + (rec.destino.name or "")
                result.append((rec.id, name))
            elif rec.name and rec.folio_cotizacion and rec.origen and rec.destino and not rec.cliente_cotizacion:
                name = (rec.folio_cotizacion or "") + '/' + (rec.name or "") + '/' + (rec.origen.name or "") + '/' + (rec.destino.name or "")
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))

        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|', '|', '|',
                    ('name', 'ilike', name),
                    ('linea_id.cotizacion_id.name', 'ilike', name),
                    ('linea_id.cotizacion_id.cliente.name', 'ilike', name),
                    ('origen.name', 'ilike', name),
                    ('destino.name', 'ilike', name)
                    ]
        result = self.search(domain + args, limit=limit)
        res = result.name_get()
        return res

    @api.constrains('cantidad')
    def _check_cantidad(self):
        if self.cantidad <= 0:
            raise UserError(_('Error !\nEn la cantidad debe ser un valor mayor 0'))

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Cotizaciones.Linea.Origen') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Cotizaciones.Linea.Origen') or _('Nuevo')
        return super(trafitec_cotizacion_line_origen, self).create(vals)



class trafitec_cotizacion_line_negociacion(models.Model):
    _name = 'trafitec.cotizacion.linea.negociacion'
    _description='cotizacion linea negociacion'
    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('con_asociado', 'Con asociado'),
            ('con_tiporemolque', 'Con tipo de remolque'),
            ('con_asociado_tiporemolque', 'Con asociado y tipo de remolque')
        ],
        default='con_asociado',
        required=True
    )
    asociado_id = fields.Many2one('res.partner', domain="[('asociado','=',True)]", string="Asociado")
    tarifa = fields.Float(string='Tarifa para este asociado', required=True, index=True)
    tarifac = fields.Float(string='Tarifa para cliente', required=True, index=True)
    detalles = fields.Text(string='Detalles')
    linea_id = fields.Many2one('trafitec.cotizaciones.linea')
    tiporemolque_id = fields.Many2one(string="Tipo remolque", comodel_name='trafitec.moviles')
    state = fields.Selection(string="Estado", selection=[('noautorizado', 'No autorizado'), ('autorizado', 'Autorizado')], default='noautorizado', help='Estado de la negociación.')

    #_sql_constraints = [('name_unique', 'unique(linea_id,asociado_id, tiporemolque_id)', 'No se permite registrar 2 o mas negociaciones a un mismo asociado y mismo tipo de remolque.'),]

    @api.constrains(
        'tarifa'
    )
    @api.constrains(
        'tarifa'
    )
    def _check_tarifa(self):
        if self.tarifa <= 0:
            raise UserError(_('Error !\nLa tarifa debe ser un valor mayor 0'))

    @api.model
    def create(self, vals):
        """
        obj_nego = self.env['trafitec.cotizacion.linea.negociacion'].search(
            [
                ('asociado_id', '=', vals['asociado_id']),
                ('tiporemolque_id', '=', vals['tiporemolque_id']),
                ('linea_id', '=', vals['linea_id'])
            ]
        )

        if len(obj_nego) > 0:
            raise UserError(_('Error !\nNo se permite registrar 2 o mas negociaones a un mismo asociado y mismo tipo de remolque.'))
        """
        return super(trafitec_cotizacion_line_negociacion, self).create(vals)

    
    def write(self, vals):
        """
        if 'asociado_id' in vals:
            asociado_id = vals['asociado_id']
            if asociado_id != self.asociado_id.id:
                obj_nego = self.env['trafitec.cotizacion.linea.negociacion'].search(
                    [
                    ('asociado_id', '=', asociado_id),
                    ('tiporemolque_id', '=', vals['tiporemolque_id']),
                    ('linea_id', '=', self.linea_id.id)
                    ]
                )
                if len(obj_nego) > 0:
                    raise UserError(_('Error !\nNo se permite registrar 2 o mas negociaones a un asociado'))
        """
        return super(trafitec_cotizacion_line_negociacion, self).write(vals)


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

class trafitec_cotizaciones_evidencias(models.Model):
    _name = 'trafitec.cotizaciones.evidencias'
    _description='evidencias cotizaciones'
    image_filename = fields.Char("Nombre del archivo")
    evidencia_file = fields.Binary(string="Archivo", required=True)
    cotizacion_id = fields.Many2one(comodel_name="trafitec.cotizacion", string="Cotización", ondelete='cascade')

class trafitec_cotizaciones_documentos(models.Model):
    _name = 'trafitec.cotizaciones.documentos'
    _description='cotizaciones documentos'
    cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion', help='Cotización')
    tipodocumento_id = fields.Many2one(string='Tipo de documento', comodel_name='trafitec.tipodoc', required=True, help='Tipo de documento')

    tipo_tipo = fields.Selection(string='Tipo', related='tipodocumento_id.tipo')
    tipo_evidencia = fields.Boolean(string='Evidencia', related='tipodocumento_id.evidencia')
    tipo_dmc = fields.Boolean(string='DMC', related='tipodocumento_id.dmc')
