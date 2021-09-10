# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from datetime import timedelta


class TrafitecCrmTraficoWizard(models.TransientModel):
    _name = "trafitec.crm.trafico.wizard"
    _order = "id desc"
    _description ="CRM Trafico Wizard"

    name = fields.Char(
        string="Nombre", 
        default="", 
        required=True
    )
    buscar_folio = fields.Char(string="Folio")
    buscar_producto = fields.Char(string="Producto")
    buscar_origen = fields.Char(string="Origen")
    buscar_destino = fields.Char(string="Destino")
    buscar_cliente = fields.Char(string="Cliente")
    buscar_asociado = fields.Char(string="Asociado")
    buscar_fechai = fields.Date(
        string="Fecha inicial", 
        default=datetime.datetime.today() + timedelta(days=-7)
    )
    buscar_fechaf = fields.Date(
        string="Fecha final", 
        default=datetime.datetime.today()
    )
    buscar_lineanegocio_id = fields.Many2one(
        string="Línea de negocio", 
        comodel_name="trafitec.lineanegocio", 
        default=1
    )

    def _calculado(self):
        self.name = "AUTOMATICO"
        self.action_buscar_cotizaciones2()

    calculado = fields.Char(
        string="", 
        compute=_calculado
    )

    def _viajes_info(self):
        info = ""
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
            tarifa_maxima, tarifa_promedio)

        return info

    def action_buscar_cotizaciones2(self):
        cotiaciones = []
        filtro = []
        self.cotizaciones_abiertas_id = None

        filtro.append(("linea_id.cotizacion_id.state", "=", "Disponible"))
        filtro.append(("linea_id.cotizacion_id.mostrar_en_crm_trafico", "=", True))
        filtro.append(("linea_id.cotizacion_id.lineanegocio", "!=", 3)) # No mostrar contenedores.
        filtro.append(("state", "=", "Disponible")) # No mostrar contenedores.

        cotizacion_linea_obj = self.env["trafitec.cotizaciones.linea"]
        cotizacion_linea_origen_obj = self.env["trafitec.cotizaciones.linea.origen"]
        viajes_obj = self.env["trafitec.viajes"]

        cotizacion_linea_origen_dat = cotizacion_linea_origen_obj.search(filtro, limit=1000)

        for clo in cotizacion_linea_origen_dat:
            viajes_dat = viajes_obj.search([("subpedido_id.id", "=", clo.id)])

            totalviajes = 0.0

            for v in viajes_dat:
                totalviajes += v.peso_origen_total / 1000

            cotiaciones.append(
                {
                    "crm_trafico_id": self.id,
                    "folio": clo.linea_id.cotizacion_id.name,
                    "fecha": clo.linea_id.cotizacion_id.fecha,
                    "origen": clo.origen.name,
                    "destino": clo.destino.name,
                    "producto": clo.linea_id.cotizacion_id.product.name,
                    "tarifa_a": clo.linea_id.tarifa_asociado,
                    "cliente": clo.linea_id.cotizacion_id.cliente.name,
                    "usuarios_asignados": reduce(lambda txt, item: txt + "(" + (item.name or "") + ") ", clo.linea_id.cotizacion_id.user_ids, ""),
                    "peso": clo.cantidad,
                    "peso_viajes": totalviajes,
                    "cotizacion_id": clo.linea_id.cotizacion_id.id,
                    "cotizacion_linea_id": clo.linea_id.id,
                    "avance": totalviajes * 100 / clo.cantidad,
                    "detalles": clo.linea_id.detalle_asociado,
                    "semaforo_valor": clo.linea_id.cotizacion_id.semaforo_valor,
                    "lineanegocio": clo.linea_id.cotizacion_id.lineanegocio.name,
                    "estado": clo.linea_id.cotizacion_id.state
                }
            )

        self.cotizaciones_abiertas_id = None
        self.cotizaciones_abiertas_id = cotiaciones

    viajes_info = fields.Html(
        string="Info", 
        default="", 
        readonly=True
    )
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

    def action_buscar_viajes(self):
        if not self.buscar_fechai or not self.buscar_fechaf:
            raise UserError(_("Debe especificar el periodo de fechas."))

        viajes = []
        filtro = []
        self.resultados_id = None

        info = ""
        tarifa_minima = 0
        tarifa_maxima = 0
        tarifa_promedio = 0
        tarifa_total = 0

        if self.buscar_folio:
            filtro.append(("name", "ilike", "%" + self.buscar_folio + "%"))

        if self.buscar_producto:
            filtro.append(("product.name", "ilike", "%" + self.buscar_producto + "%"))

        if self.buscar_cliente:
            filtro.append(("cliente_id.name", "ilike", "%" + self.buscar_cliente + "%"))

        if self.buscar_asociado:
            filtro.append(("asociado_id.name", "ilike", "%" + self.buscar_asociado + "%"))

        if self.buscar_origen:
            filtro.append(("origen.name", "ilike", "%" + self.buscar_origen + "%"))

        if self.buscar_destino:
            filtro.append(("destino.name", "ilike", "%" + self.buscar_destino + "%"))

        if self.buscar_lineanegocio_id:
            filtro.append(("lineanegocio", "=", self.buscar_lineanegocio_id.id))

        filtro.append(("fecha_viaje", ">=", self.buscar_fechai))
        filtro.append(("fecha_viaje", "<=", self.buscar_fechaf))

        filtro.append(("state", "=", "Nueva"))

        viajes_obj = self.env["trafitec.viajes"]
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
                    "folio": v.name,
                    "fecha": v.fecha_viaje,
                    "origen": v.origen.name,
                    "destino": v.destino.name,
                    "producto": v.product.name,
                    "asociado": v.asociado_id.name,
                    "tarifa_a": v.tarifa_asociado,
                    "cliente": v.cliente_id.name,
                    "viaje_id": v.id,
                    "peso": v.peso_origen_total / 1000,
                    "estado": v.state
                }
            )

        if len(viajes_dat) > 0:
            tarifa_promedio = tarifa_total / len(viajes_dat)

        info = "<b>Tarifa mínima: </b><font color="green">{0:,.2f}</font> <b>Tarifa máxima</b>: <font color="red">{1:,.2f}</font> <b>Tarifa promedio: </b>{2:,.2f}".format(
            tarifa_minima, tarifa_maxima, tarifa_promedio)

        self.viajes_info = info
        self.resultados_id = None
        self.resultados_id = viajes

    @api.model
    def retrieve_sales_dashboard(self):
        """ Fetch data to setup Sales Dashboard """
        result = {
            "meeting": {"today": 0, "next_7_days": 4.5, },
            "activity": {"today": 0, "overdue": 0, "next_7_days": 4, },
            "closing": {"today": 0, "overdue": 0, "next_7_days": 5, },
            "done": {"this_month": 0, "last_month": 0, },
            "won": {"this_month": 0, "last_month": 0, }, "nb_opportunities": 0, 
        }

        return result