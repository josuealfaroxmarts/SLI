from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from datetime import timedelta


class TrafitecCrmTrafico(models.TransientModel):
    _name = 'trafitec.crm.trafico'
    _order = 'id desc'
    _description = 'crm trafico'

    name = fields.Char(
        string='Nombre',
        default='',
        required=True
    )
    buscar_folio = fields.Char(string='Folio')
    buscar_producto = fields.Char(string='Producto')
    buscar_origen = fields.Char(string='Origen')
    buscar_destino = fields.Char(string='Destino')
    buscar_cliente = fields.Char(string='Cliente')
    buscar_asociado = fields.Char(string='Asociado')
    buscar_fechai = fields.Date(
        string='Fecha inicial',
        default=datetime.datetime.today() + timedelta(days=-7)
    )
    buscar_fechaf = fields.Date(
        string='Fecha final',
        default=datetime.datetime.today()
    )
    buscar_lineanegocio_id = fields.Many2one(
        string='Línea de negocio',
        comodel_name='trafitec.lineanegocio',
        default=1
    )
    calculado = fields.Char(string='', compute=_calculado)

    viajes_info = fields.Html(string='Info', default='', readonly=True)
    resultados_id = fields.One2many(
        string="Resultado",
        comodel_name="trafitec.crm.trafico.resultado",
        inverse_name="crm_trafico_id"
    )
    cotizaciones_abiertas_id = fields.One2many(
        string="Cotizaciones",
        comodel_name="trafitec.crm.trafico.pedidos",
        inverse_name="crm_trafico_id"
    )

    def _calculado(self):
        for rec in self:
            rec.name = "AUTOMATICO"
            rec.action_buscar_cotizaciones2()

    def _viajes_info(self):
        for rec in self:
            info = ''
            tarifa_minima = 0
            tarifa_maxima = 0
            tarifa_promedio = 0
            tarifa_total = 0
            for v in rec.resultados_id:
                tarifa_total += v.tarifa_a
                if v.tarifa_a > tarifa_maxima:
                    tarifa_maxima = v.tarifa_a
                if v.tarifa_a < tarifa_minima:
                    tarifa_minima = v.tarifa_a
            tarifa_promedio = tarifa_total / len(rec.resultados_id)
            info = (
                "<b>Tarifa mínima:</b>{0:.2f} Tarifa máxima:{0:.2f}".format(
                    tarifa_minima,
                    tarifa_maxima
                )
                + " Tarifa promedio:{0:.2f}".format(tarifa_promedio)
            )
            return info

    def action_buscar_cotizaciones2(self):
        for rec in self:
            cotiaciones = []
            filtro = []
            rec.cotizaciones_abiertas_id = None
            filtro.append(('linea_id.cotizacion_id.state', '=', 'Disponible'))
            filtro.append(
                ('linea_id.cotizacion_id.mostrar_en_crm_trafico', '=', True)
            )
            filtro.append(('linea_id.cotizacion_id.lineanegocio', '!=', 3))
            filtro.append(('state', '=', 'Disponible'))
            cotizacion_linea_obj = self.env['trafitec.cotizaciones.linea']
            cotizacion_linea_origen_obj = self.env[
                'trafitec.cotizaciones.linea.origen'
            ]
            viajes_obj = self.env['trafitec.viajes']
            cotizacion_linea_origen_dat = cotizacion_linea_origen_obj.search(
                filtro,
                limit=1000
            )
            for clo in cotizacion_linea_origen_dat:
                viajes_dat = viajes_obj.search([
                    ('subpedido_id.id', '=', clo.id)
                ])
                totalviajes = 0.0
                for v in viajes_dat:
                    totalviajes += v.peso_origen_total / 1000
                cotiaciones.append(
                    {
                        'crm_trafico_id': rec.id,
                        'folio': clo.linea_id.cotizacion_id.name,
                        'fecha': clo.linea_id.cotizacion_id.fecha,
                        'origen': clo.origen.name,
                        'destino': clo.destino.name,
                        'producto': clo.linea_id.cotizacion_id.product.name,
                        'tarifa_a': clo.linea_id.tarifa_asociado,
                        'cliente': clo.linea_id.cotizacion_id.cliente.name,
                        'usuarios_asignados': reduce(
                            lambda txt, item:
                                txt + '(' + (item.name or '') + ') ',
                                clo.linea_id.cotizacion_id.user_ids, ""
                        ),
                        'peso': clo.cantidad,
                        'peso_viajes': totalviajes,
                        'cotizacion_id': clo.linea_id.cotizacion_id.id,
                        'cotizacion_linea_id': clo.linea_id.id,
                        'avance': totalviajes * 100 / clo.cantidad,
                        'detalles': clo.linea_id.detalle_asociado,
                        'semaforo_valor': (
                            clo.linea_id.cotizacion_id.semaforo_valor
                        ),
                        'lineanegocio': (
                            clo.linea_id.cotizacion_id.lineanegocio.name
                        ),
                        'estado': clo.linea_id.cotizacion_id.state
                    }
                )
            rec.cotizaciones_abiertas_id = None
            rec.cotizaciones_abiertas_id = cotiaciones

    def action_buscar_viajes(self):
        for rec in self:
            if not rec.buscar_fechai or not rec.buscar_fechaf:
                raise UserError("Debe especificar el periodo de fechas.")
            viajes = []
            filtro = []
            rec.resultados_id = None
            info = ''
            tarifa_minima = 0
            tarifa_maxima = 0
            tarifa_promedio = 0
            tarifa_total = 0
            if rec.buscar_folio:
                filtro.append(('name', 'ilike', '%' + rec.buscar_folio + '%'))
            if rec.buscar_producto:
                filtro.append(
                    ('product.name', 'ilike', '%' + rec.buscar_producto + '%')
                )
            if rec.buscar_cliente:
                filtro.append((
                    'cliente_id.name',
                    'ilike',
                    '%' + rec.buscar_cliente + '%'
                ))
            if rec.buscar_asociado:
                filtro.append((
                    'asociado_id.name',
                    'ilike',
                    '%' + rec.buscar_asociado + '%'
                ))
            if rec.buscar_origen:
                filtro.append((
                    'origen.name',
                    'ilike',
                    '%' + rec.buscar_origen + '%'
                ))
            if rec.buscar_destino:
                filtro.append((
                    'destino.name',
                    'ilike',
                    '%' + rec.buscar_destino + '%'
                ))
            if rec.buscar_lineanegocio_id:
                filtro.append((
                    'lineanegocio',
                    '=',
                    rec.buscar_lineanegocio_id.id
                ))
            filtro.append(('fecha_viaje', '>=', rec.buscar_fechai))
            filtro.append(('fecha_viaje', '<=', rec.buscar_fechaf))
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
            info = (
                "<b>Tarifa mínima: </b><font color='green'>{0:,.2f}".format(
                    tarifa_minima
                )
                + "</font> <b>Tarifa máxima</b>: <font color='red'>"
                + "{0:,.2f}</font> <b>Tarifa promedio: </b>{1:,.2f}".format(
                    tarifa_maxima,
                    tarifa_promedio
                )
            )
            rec.viajes_info = info
            rec.resultados_id = None
            rec.resultados_id = viajes

    @api.model
    def retrieve_sales_dashboard(self):
        """ Fetch data to setup Sales Dashboard """
        result = {
            'meeting': {'today': 0, 'next_7_days': 4.5, },
            'activity': {'today': 0, 'overdue': 0, 'next_7_days': 4, },
            'closing': {'today': 0, 'overdue': 0, 'next_7_days': 5, },
            'done': {'this_month': 0, 'last_month': 0, },
            'won': {'this_month': 0, 'last_month': 0, },
            'nb_opportunities': 0,
        }
        return result
