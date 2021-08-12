# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class TrafitecCotizacion(models.Model):
    _name = 'trafitec.cotizacion'
    _description = 'cotizacion'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='No. Cotización',
        copy=False,
        readonly=True
    )
    nombre = fields.Char(string='Nombre')
    colonia = fields.Char(string='Colonia')
    estado = fields.Char(string='Estado')
    codigo_postal = fields.Char(string='Código postal')
    ciudad = fields.Char(string='Ciudad')
    presentacion_carga = fields.Selection(
        [
            ('Granel', 'Granel'),
            ('Costal', 'Costal'),
            ('Contenedor', 'Contenedor')
        ],
        string='Presentación de carga'
    )
    lineanegocio = fields.Many2one(
        'trafitec.lineanegocio',
        string='Linea de negocios',
        tracking=True
    )
    contacto = fields.Char(
        string='Contacto referenciado',
        required=False,
        tracking=True
    )
    contacto2 = fields.Many2one(
        string='Contacto',
        comodel_name='res.partner',
        tracking=True
    )
    email = fields.Char(
        string='Email',
        tracking=True
    )
    telefono = fields.Char(
        string='Teléfono',
        tracking=True
    )
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    validohasta = fields.Date(
        string='Válido hasta',
        tracking=True
    )
    cliente_refenciado = fields.Char(
        string='Cliente referenciado',
        tracking=True
    )
    cliente = fields.Many2one(
        'res.partner',
        string='Cliente',
        domain=[
            ('customer', '=', 1),
            ('parent_id', '=', False)
        ],
        tracking=True
    )
    direccion = fields.Many2one(
        'res.partner',
        string='Dirección',
        domain=[
            '|', ('parent_id', '=', cliente),
            ('id', '=', cliente)
        ],
        tracking=True
    )
    product = fields.Many2one(
        'product.product',
        string='Producto',
        tracking=True
    )
    producto_referen = fields.Char(
        string='Producto referenciado',
        tracking=True
    )
    origen_id = fields.Many2one(
        'trafitec.ubicacion',
        string='Ubicación origen',
        tracking=True,
        domain=[
            ('cliente_ubicacion', '=', cliente)
        ]
    )
    destino_id = fields.Many2one(
        'trafitec.ubicacion',
        string='Ubicación destino',
        tracking=True,
        domain=[
            ('cliente_ubicacion', '=', cliente)
        ]
    )
    lavada = fields.Boolean(string='Lavada')
    fumigada = fields.Boolean(string='Fumigada')
    limpia = fields.Boolean(string='Limpia')
    otro = fields.Boolean(string='Otro')
    otro_texto = fields.Char(string='Otro texto')
    camisa = fields.Selection([
            ('false', 'No aplica'),
            ('corta', 'Manga corta'),
            ('larga', 'Manga Larga')
        ],
        default='false'
    )
    tipo_camion = fields.One2many(
        'trafitec.type_truck',
        'tipo_camion'
    )
    material_especial = fields.Char(string='Material Especial')
    chaleco = fields.Selection([
        ('No', 'No'),
        ('Si', 'Si')
    ])
    color_chaleco = fields.Char(string='Color del chaleco')
    calzado = fields.Selection([
            ('No', 'No'),
            ('Si', 'Si')
        ]
    )
    lentes_seguridad = fields.Boolean(string='Lentes de seguridad')
    casco = fields.Boolean(string='Casco')
    cubre_bocas = fields.Boolean(string='Cubre bocas')
    otro_operador = fields.Char(string='Otro operador')
    sua = fields.Selection([
        ('No', 'No'),
        ('Si', 'Si')
    ])
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda'
    )
    factor_seguro = fields.Float(
        string='Factor de seguro',
        digits=(16, 3),
        default=0.004
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Plazos de pago'
    )
    pay_method_id = fields.Many2one(
        'pay.method',
        string='Metodo de pago'
    )
    aplicanorma = fields.Boolean(string='Aplica norma SCT-012 por peso medido')
    seguro_mercancia = fields.Boolean(
        string='Seguro de mercancia',
        tracking=True,
        store=True
    )
    polizas_seguro = fields.Many2one(
        'trafitec.polizas',
        string='Póliza de seguro',
        tracking=True
    )
    porcen_seguro = fields.Float(
        string='Porcentaje de seguro',
        tracking=True
    )
    seguro_entarifa = fields.Boolean(
        string='Seguro en tarifa',
        tracking=True,
        help='El seguro va incluido en la tarifa.'
    )
    costo_producto = fields.Float(
        string='Costo del producto',
        required=True,
        tracking=True
    )
    reglas_merma = fields.Selection([
            ('No cobrar', 'No cobrar'),
            ('Porcentaje: Cobrar diferencia', '% Cobrar diferencia'),
            ('Porcentaje: Cobrar todo', '% Cobrar Todo'),
            ('Kg: Cobrar diferencia', 'Kilogramos cobrar diferencia'),
            ('Kg: Cobrar todo', 'Kilogramos cobrar todo'),
            ('Cobrar todo', 'Cobrar Todo')
        ],
        string='Reglas de merma'
    )
    lista_precio = fields.Many2one(
        'product.pricelist',
        string='Lista de precios',
        tracking=True
    )

    iva = fields.Many2one(
        'account.tax',
        string='IVAS'
    )
    state = fields.Selection([
            ('Nueva', 'Nueva'),
            ('Autorizada', 'Autorizada'),
            ('Enviada', 'Enviada'),
            ('Disponible', 'Disponible'),
            ('EnEspera', 'En espera'),
            ('Cancelada', 'Cancelada'),
            ('Cerrada', 'Cerrada')
        ],
        string='Estados',
        default='Nueva',
        tracking=True
    )
    lineas_cotizacion_id = fields.One2many(
        'trafitec.cotizaciones.linea',
        'cotizacion_id',
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'trafitec.cotizacion')
    )
    motivo_cancelacion = fields.Text(
        string='Motivo cancelacion',
        tracking=True
    )
    fecha_cancelacion = fields.Datetime(
        string='Fecha de cancelacion',
        tracking=True
    )
    x_folio_trafitecw = fields.Char(
        string='Folio Trafitec Windows',
        help='Folio de la orden de carga en Trafitec para windows.',
        tracking=True
    )
    sucursal_id = fields.Many2one(
        'trafitec.sucursal',
        string='Sucursal',
        tracking=True
    )
    evidencia_id = fields.One2many(
        string='Evidencias',
        comodel_name='trafitec.cotizaciones.evidencias',
        inverse_name='cotizacion_id',
        tracking=True
    )

    detalles = fields.Text(
        string='Detalles',
        default='',
        tracking=True
    )
    odoo_cotizacion_id = fields.Many2one(
        string='Cotización odoo',
        comodel_name='sale.order'
    )
    cliente_plazo_pago_id = fields.Many2one(
        string='Plazo de pagos de cliente',
        comodel_name='account.payment.term'
    )
    asociado_plazo_pago_id = fields.Many2one(
        string='Plazo de pagos de asociado',
        comodel_name='account.payment.term'
    )
    semaforo_valor = fields.Selection([
            ('verde', 'Verde'),
            ('amarillo', 'Amarillo'),
            ('rojo', 'Rojo')
        ],
        string='Semáforo',
        default='verde',
        tracking=True
    )
    mostrar_en_crm_trafico = fields.Boolean(
        string='Mostrar en CRM Tráfico',
        help='Indica si la cotización se mostrara en el CRM Tráfico.',
        default=False
    )
    documentos_id = fields.One2many(
        string='Documentos requeridos',
        comodel_name='trafitec.cotizaciones.documentos',
        inverse_name='cotizacion_id',
        help='Documentos requeridos.'
    )
    cliente_bloqueado = fields.Boolean(
        string='Cliente bloqueado',
        related='cliente.bloqueado_cliente_bloqueado',
        store=True,
        default=False,
        help='Indica si el cliente esta bloqueado.'
    )
    folio = fields.Char(
        string='Folio',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    monto_total = fields.Float(
        string='Monto Total aproximado',
        readonly=True,
        compute=_monto_total,
        store=True
    )
    monto_inicial = fields.Float(
        string='Monto Final',
        readonly=True,
        store=True,
        default=0.00
    )

    def action_enviarcorreo_autorizacion(self):
        for rec in self:
            asunto = 'Cotización por autorizar: '+str(rec.name or '')
            de = (self.env.user.login or '')
            para = rec.create_uid.login
            contenido = ''
            empleado = None
            jefe = None
            cliente = None
            empleado = self.env['hr.employee'].search([
                    ('user_id', '=', rec.env.user.id)
                ],
                limit=1
            )
            if empleado:
                jefe = empleado.parent_id
            if jefe:
                para = (jefe.work_email or '')
            cliente = (rec.cliente.name or rec.cliente_refenciado or '')
            contenido = (
                'Estimado '
                + str(jefe.name or '')
                + ' el usuario '
                + str(empleado.name or '')
                + ' solicita la autorización de la cotización con folio: '
                + str(self.name or '')
                + ' para el cliente: '
                + str(cliente or '')
                + ' Odoo: http://odoo.sli.mx.'
            )
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
        for rec in self:
            rec.email = rec.contacto2.email
            rec.telefono = rec.contacto2.phone or rec.contacto2.mobile

    def action_enviar_info_cliente(self):
        for rec in self:
            contenido = ''
            para = ''
            para2 = ''
            contenido += ''
            sql = ''
            lista = []
            sql = '''
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
            '''.format(rec.id)
            self.env.cr.execute("sql")
            lista = self.env.cr.dictfetchall()
            glo = self.env['trafitec.glo']
            if not rec.contacto and not rec.contacto2:
                raise UserError(_(
                    'La cotización no tiene especificado el contacto.'
                ))
            if not rec.email:
                raise UserError(_(
                    'La cotización no tiene especificado el correo del '
                    + 'contacto.'
                ))
            else:
                if '@' not in rec.email:
                    raise UserError(_(
                        'El correo del contacto es incorrecto: '
                        + str(rec.email or '')
                    ))
            estilo_noborde = (
                'border-style: none; border-color:silver; border-width:0px;'
            )
            estilo_borde = (
                'border-style: dotted; border-color:silver; border-width:1px;'
                + ' padding:5px;'
            )
            estilo_borde_redondo = (
                'border-style: none; border-color:none; brder-width:0px; '
                + 'padding:5px; border-radius:10px;'
            )
            estilo_fondo_cabecera = 'background-color: red; color:white;'
            estilo_fondo_subtotal = (
                'background-color: #cccccc; color:black;'
                + estilo_borde_redondo
            )
            estilo_texto = (
                'font-size: 12px; text-align:right; font-family:arial;'
            )
            estilo_texto_negritas = estilo_texto + 'font-weight: bold;'
            estilo_etiqueta = estilo_texto + 'font-weight: bold;'
            estilo = (
                'font-size: 12px; text-align:right; font-family:arial; '
                + 'font-weight: bold;'
                + estilo_fondo_subtotal
            )
            estilo_fondo = (
                'background-color:silver; font-size: 12px; font-family:arial;'
                + estilo_noborde
            )
            estilo_normal = (
                'font-size: 12px; font-family:arial;'
                + estilo_borde
            )
            estilo_cabecera = (
                'font-size: 12px; font-family:arial;'
                + estilo_borde_redondo
                + estilo_fondo_cabecera
            )
            estilo_normal_origen_destino = (
                'font-size: 10px; font-family:arial;'
                + estilo_borde
            )
            estilo_moneda_rojo = (
                'font-size: 12px; text-align:right; font-family:arial; color:'
                + ' red;'
                + estilo_borde
            )
            estilo_moneda_verde = (
                'font-size: 12px; text-align:right; font-family:arial; color:'
                + ' green;'
                + estilo_borde
            )
            estilo_tons = (
                'font-size: 12px; text-align:right; font-family:arial;'
                + estilo_borde
            )
            estilo_tons_subtotal = (
                'font-size: 12px; text-align:right; font-family:arial; '
                + 'font-weight: bold;'
                + estilo_noborde + estilo_fondo_subtotal
            )
            estilo_hr = (
                'border-color:#dddddd; border-style:dotted;'
                + estilo_borde
            )
            lineas_obj = self.env['trafitec.cotizaciones.linea']
            origendestino_obj = self.env['trafitec.cotizaciones.linea.origen']
            viajes_obj = self.env['trafitec.viajes']
            lineas_dat = lineas_obj.search([('cotizacion_id', '=', rec.id)])
            origendestino_dat = None
            viajes_dat = None
            contenido = ''
            contenido += "<img src='http://sli.mx/media/logo.png'/><br/>"
            contenido += '<b>SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV</b>'
            contenido += "<hr style='{0}'/>".format(estilo_hr)
            contenido += (
                'CLIENTE: '
                + str(rec.cliente.name or rec.cliente_refenciado or '')
                + '<br/>'
            )
            contenido += 'PEDIDO: ' + str(rec.name or '') + '<br/>'
            contenido += (
                'LINEA NEGOCIO: '
                + str(self.lineanegocio.name or '')
                + '<br/>'
            )
            contenido += "<hr style='{0}'/>".format(estilo_hr)
            contenido += (
                'Estimado(a) {0} por este medio le hacemos llegar el avance'
                + ' general del pedido con folio {1}.'.format(
                    (rec.contacto or rec.contacto2.name),
                    rec.name
                )
            )
            contenido += "<hr style='{0}'/>".format(estilo_hr)
            cantidad = 0
            contenido += '<table border=0 cellspacing=1>'
            contenido += '<tr>'
            if rec.lineanegocio.id == 1:
                contenido += (
                    "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'"
                    + ">ORIGEN</th><th style='{0}'>DESTINO</th><th "
                    + "style='{0}'>TONS A MOVER</th><th style='{0}'>"
                    + "TONS MOVIDAS</th><th style='{0}'>TONS SALDO</th>"
                    + "<th style='{0}'>AVANCE (%)</th>".format(
                        estilo_cabecera
                    )
                )
            elif rec.lineanegocio.id == 2:
                contenido += (
                    "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'>ORIGEN"
                    + "</th><th style='{0}'>DESTINO</th><th style='{0}'>"
                    + "VIAJES A MOVER</th><th style='{0}'>VIAJES REALIZADOS"
                    + "</th><th style='{0}'>VIAJES SALDO</th><th style='{0}'>"
                    + "AVANCE (%)</th>".format(estilo_cabecera)
                )
            else:
                contenido += (
                    "<th style='{0}'>FOLIO CLIENTE</th><th style='{0}'>ORIGEN"
                    + "</th><th style='{0}'>DESTINO</th><th style='{0}'>"
                    + "CONTENEDORES A MOVER</th><th style='{0}'>CONTENEDORES"
                    + " MOVIDOS</th><th style='{0}'>CONTENEDORES SALDO</th>"
                    + "<th style='{0}'>AVANCE (%)</th>".format(
                        estilo_cabecera
                    )
                )
            contenido += '</tr>'
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
                folio_cliente = ''
                destino_act_id = od.get('destino_id', -1)
                cantidad = od.get('cantidad', 0)
                peso = od.get('peso_origen_tons', 0)
                folio_cliente = od.get('folio_cliente', '')
                origen = od.get('origen_nombre', '')
                destino = od.get('destino_nombre', '')
                total_cantidad += cantidad
                total_peso += peso
                if destino_act_id != destino_ant_id:
                    subtotal_saldo = subtotal_cantidad - subtotal_peso
                    if subtotal_cantidad > 0:
                        subtotal_avance = (
                            subtotal_peso * 100 / subtotal_cantidad
                        )
                    contenido += '<tr>'
                    contenido += "<td style='{0}'></td>".format(estilo_noborde)
                    contenido += "<td style='{0}'></td>".format(estilo_noborde)
                    contenido += "<td style='{0}'>SUBTOTAL</td>".format(
                        estilo_etiqueta + estilo_noborde
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_cantidad or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_peso or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_saldo or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(
                        estilo,
                        (subtotal_avance or 0)
                    )
                    contenido += '</tr>'
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
                contenido += '<tr>'
                contenido += "<td style='{0}'>{1}</td>".format(
                    estilo_normal,
                    str(folio_cliente or '')
                )
                contenido += "<td style='{0}'>{1}</td>".format(
                    estilo_normal_origen_destino,
                    str(origen or '')
                )
                contenido += "<td style='{0}'>{1}</td>".format(
                    estilo_normal_origen_destino,
                    str(destino or '')
                )
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                    estilo_tons,
                    (cantidad or 0)
                )
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                    estilo_tons,
                    (peso or 0)
                )
                contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                    estilo_tons,
                    (saldo or 0)
                )
                contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(
                    estilo,
                    (avance or 0)
                )
                contenido += '</tr>'
                if c == len(lista):
                    subtotal_saldo = subtotal_cantidad - subtotal_peso
                    if subtotal_cantidad > 0:
                        subtotal_avance = (
                            subtotal_peso * 100 / subtotal_cantidad
                        )
                    contenido += '<tr>'
                    contenido += "<td style='{}'></td>".format(estilo_noborde)
                    contenido += "<td style='{}'></td>".format(estilo_noborde)
                    contenido += "<td style='{}'>SUBTOTAL</td>".format(
                        estilo_etiqueta + estilo_noborde
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_cantidad or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_peso or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                        estilo_tons_subtotal,
                        (subtotal_saldo or 0)
                    )
                    contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(
                        estilo,
                        (subtotal_avance or 0)
                    )
                    contenido += '</tr>'
                    subtotal_cantidad = 0
                    subtotal_peso = 0
                destino_ant_id = od.get('destino_id', -1)
            total_saldo = total_cantidad - total_peso
            if total_cantidad > 0:
                total_avance = total_peso * 100 / total_cantidad
            contenido += '<tr>'
            contenido += "<td style='{0}'></td>".format(estilo_noborde)
            contenido += "<td style='{0}'></td>".format(estilo_noborde)
            contenido += "<td style='{0}'>TOTAL</td>".format(
                estilo_etiqueta + estilo_noborde
            )
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                estilo_tons_subtotal,
                (total_cantidad or 0)
            )
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                estilo_tons_subtotal,
                (total_peso or 0)
            )
            contenido += "<td style='{0}'>{1:20,.3f}</td>".format(
                estilo_tons_subtotal,
                (total_saldo or 0)
            )
            contenido += "<td style='{0}'>{1:20,.2f}%</td>".format(
                estilo,
                (total_avance or 0)
            )
            contenido += '</tr>'
            contenido += '</table>'
            cfg = glo.cfg()
            para = rec.email
            para2 = rec.create_uid.login
            if cfg:
                if (
                    cfg.cot_envio_avance_pruebas_st
                    and cfg.cot_envio_avance_pruebas_correo
                ):
                    para = cfg.cot_envio_avance_pruebas_correo
                    para2 = ''
            if ('@' in para) or ('@' in para2):
                rec.enviar_correo(
                    asunto='SLI PEDIDO {}'.format(rec.name),
                    contenido=contenido,
                    para=para,
                    para2=para2
                )

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
        raise UserError(_('Alerta..\nNo esta permitido borrar cotizaciones.'))

    @api.depends('lineas_cotizacion_id.subtotal', 'seguro_mercancia')
    def _monto_total(self):
        for order in self:
            monto = 0
            for line in order.lineas_cotizacion_id:
                if monto == 0:
                    monto = line.subtotal
                else:
                    monto += line.subtotal
                if order.seguro_mercancia:
                    seguro_total_mercancia = (
                        order.costo_producto
                        * order.factor_seguro
                        * order.lineas_cotizacion_id.cantidad
                        * 1000
                    )
                    monto += seguro_total_mercancia
            order.update({
                'monto_total': monto
            })

    @api.constrains('cliente_refenciado', 'cliente')
    def _check_clientes(self):
        for rec in self:
            if not rec.cliente_refenciado and not rec.cliente.name:
                raise UserError(_(
                    'Aviso !\nDebe especificar un cliente referenciado o del '
                    + 'catalago de clientes.'
                ))

    @api.constrains('contacto2', 'contacto')
    def _check_contacto(self):
        for rec in self:
            if not rec.contacto and not rec.contacto2.name:
                raise UserError(_(
                    'Aviso !\nDebe especificar un contacto referenciado o del'
                    + ' catalago de contactos.'
                ))

    @api.constrains('producto_referen', 'product')
    def _check_producto(self):
        for rec in self:
            if not rec.producto_referen and not rec.product.name:
                raise UserError(_(
                    'Aviso !\nDebe especificar un producto referenciado o del'
                    + ' catalago de productos.'
                ))

    @api.onchange('product')
    def _onchange_product(self):
        for rec in self:
            try:
                rec.producto_referen = rec.product.name
            except:
                pass
            rec.costo_producto = rec.product.product_tmpl_id.list_price

    def _valida_moroso(self, vals=None):
        if not vals:
            return
        for rec in self:
            persona_id = vals.get('cliente', False) or rec.cliente.id
            saldo = 0.00
            es_moroso = False
            persona_obj = self.env['res.partner']
            saldo = persona_obj.saldo_vencido(persona_id)
            es_moroso = persona_obj.es_moroso(persona_id)
            if es_moroso:
                raise UserError(_(
                    'El cliente tiene facturas vencidas por: {0:.2f}.'.format(
                        saldo
                    )
                ))

    @api.model
    def create(self, vals):
        if vals.get('folio', _('New')) == _('New'):
            vals['folio'] = self.env['ir.sequence'].next_by_code(
                'trafitec.cotizacion'
            ) or _('New')
        if 'cliente' in vals:
            cliente_obj = self.env['res.partner']
            cliente_dat = cliente_obj.browse([vals.get('cliente')])
            if cliente_dat:
                if cliente_dat.bloqueado_cliente_bloqueado:
                    name = cliente_dat.bloqueado_cliente_clasificacion_id.name
                    raise UserError(_(
                        'El cliente esta bloqueado, motivo: '
                        + (name or '')
                    ))
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(
                force_company=vals['company_id']
            ).next_by_code('Trafitec.Cotizacion') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'Trafitec.Cotizacion'
            ) or _('Nuevo')
        vals['state'] = 'Nueva'
        nuevo = super(TrafitecCotizacion, self).create(vals)
        return nuevo

    @api.model
    def genera_pedido_venta(self):
        for rec in self:
            sale_order_obj = self.env['sale.order']
            sale_order_line_obj = self.env['sale.order.line']
            cliente_obj = self.env['res.partner']
            cliente_dat = cliente_obj.browse([rec.cliente.id])
            trafitec_cfg_obj = self.env['trafitec.parametros']
            trafitec_cfg_dat = trafitec_cfg_obj.search([
                ('company_id', '=', self.env.user.company_id.id)
            ])
            if not trafitec_cfg_dat.cot_producto_id:
                return
            valores = {
                'partner_id': rec.cliente.id,
                'origin': 'Cotización trafitec: ' + (rec.name or ''),
                'client_order_ref': '',
                'state': 'draft',
                'note': '',
                'product_id': trafitec_cfg_dat.cot_producto_id.id,
                'trafitec_cotizacion_id': rec.id,
                'payment_term_id': rec.payment_term_id.id,
                'team_id': cliente_dat.equipoventa_id.id
            }
            sale_order_nuevo = sale_order_obj.create(valores)
            valores = {
                'order_id': sale_order_nuevo.id,
                'order_partner_id': rec.cliente.id,
                'product_id': trafitec_cfg_dat.cot_producto_id.id,
                'product_uom_qty': 1,
                'product_uom': (
                    trafitec_cfg_dat.cot_producto_id.product_tmpl_id.uom_id.id
                ),
                'price_unit': rec.monto_total,
                'name': (sale_order_nuevo.name or '')
            }
            sale_order_line_obj.create(valores)
            sale_order_nuevo.action_confirm()
            rec.odoo_cotizacion_id = sale_order_nuevo.id

    def write(self, vals):
        for data in self:
            if 'lineanegocio' in vals:
                linea_nego_id = vals['lineanegocio']
            else:
                linea_nego_id = data.lineanegocio.id
            if 'reglas_merma' in vals:
                regla_mer = vals['reglas_merma']
            else:
                regla_mer = data.reglas_merma
            linea_nego_obj = data.env['trafitec.lineanegocio'].search([
                ('id', '=', linea_nego_id)
            ])
            if 'semaforo_valor' in vals:
                if vals['semaforo_valor'] == 'rojo':
                    correo = ''
                    try:
                        usuario = data.create_uid
                        empleado = data.env['hr.employee'].search([
                            ('user_id', '=', usuario.id)
                        ])
                        correo = empleado.parent_id.work_email
                    except:
                        pass
                    if correo != '':
                        mensaje = ''
                        mensaje += 'Cotización: {}<br/>'.format(
                            data.name or ''
                        )
                        mensaje += 'Cliente: {}<br/>'.format(
                            data.cliente.name or ''
                        )
                        mensaje += 'Producto: {}<br/>'.format(
                            data.product.name or ''
                        )
                        glo = data.env['trafitec.glo']
                        glo.enviar_correo(
                            correo,
                            'Cotización en Rojo',
                            mensaje
                        )
            return super(TrafitecCotizacion, data).write(vals)

    @api.onchange('cliente')
    def _onchange_cliente(self):
        for rec in self:
            rec.cliente_refenciado = rec.cliente.name
            if rec.cliente:
                losdocs = []
                documentos_cliente = self.env[
                    'trafitec.clientes.documentos'
                ].search([
                    ('partner_id', '=', rec.cliente.id),
                    '|',
                    ('name.evidencia', '=', True),
                    ('name.dmc', '=', True)
                ])
                for d in documentos_cliente:
                    losdocs.append({'tipodocumento_id': d.name})
                rec.documentos_id = losdocs
                if not rec.payment_term_id:
                    rec.payment_term_id = (
                        rec.cliente.property_payment_term_id.id
                    )
                if not rec.pay_method_id:
                    rec.pay_method_id = rec.cliente.pay_method_id.id
                rec.direccion = rec.cliente
                rec.reglas_merma = rec.cliente.excedente_merma
                return {
                    'domain': {
                        'domicilio': [
                            '|',
                            ('parent_id', '=', rec.cliente.id),
                            ('id', '=', rec.cliente.id)
                        ]
                    }
                }

    @api.onchange('polizas_seguro')
    def _onchange_porcentaje(self):
        for rec in self:
            if rec.polizas_seguro:
                rec.porcen_seguro = rec.polizas_seguro.porcentaje_clie

    def action_authorized(self):
        for rec in self:
            if len(self.lineas_cotizacion_id) == 0:
                raise UserError((
                    'Error !\nTiene que tener lineas antes de poder autorizar'
                    + ' esta cotizacion.'
                ))
            else:
                rec.write({'state': 'Autorizada'})

    def action_reactivate(self):
        for rec in self:
            rec.write({'state': 'Nueva'})

    def action_send(self):
        for rec in self:
            if len(rec.lineas_cotizacion_id) == 0:
                raise UserError((
                    'Error !\nTiene que tener lineas antes de poder enviar '
                    + 'esta cotizacion.'
                ))
        else:
            rec.write({'state': 'Enviada'})

    def action_accepted(self):
        for rec in self:
            if len(rec.lineas_cotizacion_id) == 0:
                raise UserError(_(
                    'Error !\nTiene que tener lineas antes de poder aceptar '
                    + 'esta cotización.'
                ))
            rec.write({'state': 'Aceptada'})

    def action_rejected(self):
        for rec in self:
            rec.write({'state': 'Rechazada'})

    def action_close(self):
        for rec in self:
            rec.write({'state': 'Cerrada'})

    def action_enespera(self):
        for rec in self:
            rec.write({'state': 'EnEspera'})

    def action_available(self):
        for rec in self:
            if rec.cliente.name:
                raise UserError(
                    'Error !\nTiene que dar de alta el cliente en el catalogo'
                    + ' y asignarlo a la cotizacion'
                )
            if not rec.product.name:
                raise UserError(
                    'Error !\nTiene que dar de alta el producto en el '
                    + 'catalogo y asignarlo a la cotizacion'
                )
            for lineas in rec.lineas_cotizacion_id:
                linea_nego_obj = self.env['trafitec.lineanegocio'].search([
                    ('id', '=', rec.lineanegocio.id)
                ])
                if (
                    linea_nego_obj.name == 'Granel'
                    or linea_nego_obj.name == 'GRANEL'
                    or linea_nego_obj.name == 'granel'
                ):
                    if not rec.reglas_merma:
                        raise UserError(
                            'Debe seleccionar una regla de merma.'
                        )
            rec.genera_pedido_venta()
            if len(rec.lineas_cotizacion_id) == 0:
                raise UserError(
                    'Error !\nTiene que tener lineas antes de poder asignar '
                    + 'esta cotizacion como disponible.'
                )
            else:
                rec.write({'state': 'Disponible'})
