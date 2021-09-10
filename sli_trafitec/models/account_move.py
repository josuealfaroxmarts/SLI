# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import datetime
from xml.dom import minidom


class AccountMove(models.Model):
    _inherit = "account.move"
    _order = "id desc"

    es_facturamanual = fields.Boolean(
        string="Es factura manual?",
        default=False
    )
    origen = fields.Char(string="Origen")
    destino = fields.Char(string="Destino")
    cliente_origen_id = fields.Many2one(
        "res.partner",
        string="Cliente origen",
        domain=[
            ("customer", "=", True),
            ("parent_id", "=", False)
        ]
    )
    domicilio_origen_id = fields.Many2one(
        "res.partner",
        string="Domicilio origen",
        domain=[
            "|", ("parent_id", "=", cliente_origen_id),
            ("id", "=", cliente_origen_id)
        ]
    )
    cliente_destino_id = fields.Many2one(
        "res.partner",
        string="Cliente destino",
        domain=[
            ("customer", "=", True),
            ("parent_id", "=", False)
        ]
    )
    domicilio_destino_id = fields.Many2one(
        "res.partner",
        string="Domicilio destino",
        domain=[
            "|", ("parent_id", "=", cliente_destino_id),
            ("id", "=", cliente_destino_id)
        ]
    )
    contiene = fields.Text(string="Contiene")
    lineanegocio = fields.Many2one(
        "trafitec.lineanegocio",
        string="Linea de negocios"
    )
    placas_id = fields.Char(string="Vehiculo")
    operador_id = fields.Char(string="Operador")
    abonado = fields.Float(string="Abonado")
    pagada = fields.Boolean(string="Pagada")
    factura_encontrarecibo = fields.Boolean(string="Factura en contra recibo")
    x_folio_trafitecw = fields.Char(string="Folio Trafitec Windows")
    es_cartaporte = fields.Boolean(
        string="Es carta porte",
        default=False
    )
    es_provision = fields.Boolean(string="Es provisión")
    contrarecibo_id = fields.Many2one(
        string="Contra recibo",
        comodel_name="trafitec.contrarecibo"
    )
    invoice_from_xml = fields.Many2one(
        "invoice.from.fletex",
        string="Factura XML",
        domain=[
            ("clientId", "=", "partner_id")
        ]
    )
    abonos = fields.Float(
        string="Abonos",
        compute="compute_abonos",
        store=True,
        help="Abonos a la factura."
    )
    cliente_bloqueado = fields.Boolean(
        string="Cliente bloqueado",
        compute="compute_bloqueado",
        default=False,
        help="Indica si el cliente esta bloqueado."
    )
    viajes_id = fields.Many2many(
        string="Viajes de trafitec",
        comodel_name="trafitec.viajes"
    )
    viajescp_id = fields.Many2many(
        string="Viajes trafitec",
        comodel_name="trafitec.viajes",
        relation="trafitec_facturas_viajescp_rel"
    )
    tipo = fields.Selection(
        string="Tipo de factura",
        selection=[
            ("normal", "Normal"),
            ("manual", "Manual"),
            ("automatica", "Automatica")
        ],
        default="normal"
    )
    total_fletes = fields.Float(
        string="Total fletes",
        store=True,
        compute="_compute_totales"
    )
    total_fletescp = fields.Float(
        string="Total de fletes",
        store=True,
        compute="_compute_totalescp"
    )
    tipo_contiene = fields.Selection(
        string="",
        selection=[
            ("ninguno", "(Ninguno)"),
            ("simple", "Simple"),
            ("detallado", "Detallado")
        ],
        default="simple"
    )
    documentos_id = fields.One2many(
        string="Documentos",
        comodel_name="trafitec.facturas.documentos",
        inverse_name="factura_id"
    )
    documentos_archivo_pdf = fields.Binary(string="Archivos PDF")
    documentos_archivo_xml = fields.Binary(
        string="Archivos XML",
        compute="_compute_documentos_tiene_xml"
    )
    documentos_nombre_pdf = fields.Char(
        string="Nombre de archivo PDF",
        default=""
    )
    documentos_nombre_xml = fields.Char(
        string="Nombre de archivo XML",
        default=""
    )
    documentos_tiene_pdf = fields.Boolean(
        string="Tiene PDF",
        default=False,
        compute="_compute_documentos_tiene_pdf",
        store=True
    )
    documentos_tiene_xml = fields.Boolean(
        string="Tiene XML",
        default=False,
        compute="_compute_documentos_tiene_xml",
        store=True
    )
    documentos_anexado_pdf = fields.Boolean(
        string="Anexado PDF",
        default=False
    )
    documentos_anexado_xml = fields.Boolean(
        string="Anexado XML",
        default=False
    )
    cancelacion_detalles = fields.Char("Motivo de cancelación")
    folios_boletas = fields.Char(
        string="Folios de boletas",
        compute="_compute_folios_boletas",
        help="Lista de folios de boletas de los viajes relacionados."
    )

    @api.depends("amount_total", "amount_residual")
    def compute_abonos(self):
        for rec in self:
            rec.abonos = rec.amount_total - rec.amount_residual

    @api.depends("partner_id.bloqueado_cliente_bloqueado")
    def compute_bloqueado(self):
        for rec in self:
            rec.cliente_bloqueado = (
                rec.partner_id.bloqueado_cliente_bloqueado or False
            )

    @api.depends("viajes_id")
    def _compute_totales(self):
        for rec in self:
            totalflete = 0.0

            for v in rec.viajes_id:
                viaje_dat = rec.env["trafitec.viajes"].search([
                    ("id", "=", v.id)
                ])
                totalflete += viaje_dat.flete_cliente

            rec.total_fletes = totalflete

    @api.depends("viajescp_id")
    def _compute_totalescp(self):
        for rec in self:
            totalflete = 0.0

            for v in rec.viajescp_id:
                numbers = [
                    int(temp)for temp in str(v.id).split() if temp.isdigit()
                ]
                viaje_dat = rec.env["trafitec.viajes"].search([
                    ("id", "=", numbers)
                ])
                totalflete += viaje_dat.flete_asociado

            rec.total_fletescp = totalflete

    @api.onchange("invoice_from_xml")
    def xml_invoice(self):
        for rec in self:

            if rec.invoice_from_xml:
                rec.documentos_archivo_xml = base64.b64decode(
                    rec.invoice_from_xml.invoiceXml
                )
                rec.documentos_archivo_pdf = rec.invoice_from_xml.invoicePdf
                rec.documentos_nombre_pdf = (
                    "Factura PDF de {} ".format(
                        rec.invoice_from_xml.clientId.name
                    )
                    + "Folio viaje: {}.pdf".format(
                        rec.invoice_from_xml.shipmentId.name
                    )
                )
                xml = minidom.parseString(base64.b64decode(
                    rec.invoice_from_xml.invoiceXml
                ))
                issuing = xml.getElementsByTagName("cfdi:Emisor")[0]
                id_account = rec.env["account.analytic.account"].search([
                    ("name", "=", "11-701-0001")
                ])
                product = rec.env["product.product"].search([
                    ("name", "=", "Flete")
                ])
                tax_one = rec.env["account.tax"].search([
                    ("amount", "=", 16.0000)
                ])
                tax_two = rec.env["account.tax"].search([
                    ("amount", "=", -4.0000)
                ])
                taxes = [tax_one[0].id, tax_two[0].id]
                voucher = xml.getElementsByTagName("cfdi:Comprobante")[0]
                subtotal = voucher.getAttribute("SubTotal")
                rec.amount_total = subtotal
                rec.invoice_date = voucher.getAttribute("Fecha")
                concepts = []
                concepts_xml = xml.getElementsByTagName("cfdi:Conceptos")[0]
                concept_xml = xml.getElementsByTagName("cfdi:Concepto")

                for x in concept_xml:
                    flete = {
                        "id": False,
                        "product_id": product.id,
                        "name": x.getAttribute("Descripcion"),
                        "quantity": x.getAttribute("Cantidad"),
                        "analytic_account_id": id_account.id,
                        "tax_ids": taxes,
                        "price_unit": subtotal,
                        "sistema": False,
                        "price_subtotal": subtotal
                    }
                    concepts = flete
                    break

                rec.invoice_line_ids = [(0, 0, concepts)]

    @api.depends("documentos_archivo_xml")
    def _compute_documentos_tiene_xml(self):
        for rec in self:

            if rec.documentos_archivo_xml:
                rec.documentos_tiene_xml = True
            else:
                rec.documentos_tiene_xml = False

    @api.depends("documentos_archivo_pdf")
    def _compute_documentos_tiene_pdf(self):
        for rec in self:

            if rec.documentos_archivo_pdf:
                rec.documentos_tiene_pdf = True
            else:
                rec.documentos_tiene_pdf = False

    def action_adjuntar_pdf(self):
        for rec in self:

            if not rec.documentos_anexado_pdf:
                rec.env["ir.attachment"].create(
                    {
                        "name": "Carta porte del asociado pdf",
                        "type": "binary",
                        "datas": rec.documentos_archivo_pdf,
                        "res_model": "account.move",
                        "res_id": rec.id,
                        "mimetype": "application/x-pdf"
                    }
                )
                rec.documentos_anexado_pdf = True
            else:
                raise UserError(("Alerta..\nEl archivo ya fue anexado."))

    def action_adjuntar_xml(self):
        for rec in self:

            if not rec.documentos_anexado_xml:
                rec.env["ir.attachment"].create(
                    {
                        "name": "Carta porte del asociado xml",
                        "type": "binary",
                        "datas": rec.documentos_archivo_xml,
                        "res_model": "account.move",
                        "res_id": rec.id,
                        "mimetype": "application/x-xml"
                    }
                )
                rec.documentos_anexado_xml = True
            else:
                raise UserError(("Alerta..\nEl archivo ya fue anexado."))

    def proceso_adjuntar_archivos(self, xid):
        if not xid:
            xid = 1000000

        facturas = self.env["account.move"].search(
            [
                "&", "&",
                ("id", ">=", xid),
                ("type", "=", "in_invoice"),
                ("state", "in", ["open"]), "|",
                ("documentos_anexado_pdf", "=", False),
                ("documentos_anexado_xml", "=", False)
            ]
        )

        if not facturas:
            return

        for f in facturas:

            if (
                not f.documentos_anexado_pdf
                and not f.documentos_archivo_pdf
                and not f.documentos_anexado_xml
                and not f.documentos_archivo_xml
            ):
                continue

            if not f.documentos_anexado_pdf and f.documentos_archivo_pdf:
                self.env["ir.attachment"].create(
                    {
                        "name": "Carta porte del asociado pdf",
                        "type": "binary",
                        "datas": f.documentos_archivo_pdf,
                        "res_model": "account.move",
                        "res_id": f.id,
                        "mimetype": "application/x-pdf"
                    }
                )
                f.documentos_anexado_pdf = True

            if not f.documentos_anexado_xml and f.documentos_archivo_xml:
                self.env["ir.attachment"].create(
                    {
                        "name": "Carta porte del asociado xml",
                        "type": "binary",
                        "datas": f.documentos_archivo_xml,
                        "res_model": "account.move",
                        "res_id": f.id,
                        "mimetype": "application/x-xml"
                    }
                )
                f.documentos_anexado_xml = True

    @api.onchange("es_facturamanual", "partner_id")
    def _onchange_partner_trafitec(self):
        for rec in self:

            if rec.es_facturamanual:
                rec.cliente_origen_id = rec.partner_id
                rec.domicilio_origen_id = rec.partner_id
                rec.cliente_destino_id = rec.partner_id
                rec.domicilio_destino_id = rec.partner_id

    @api.onchange("partner_id")
    def _onchange_partner_trafitec(self):
        for rec in self:
            rec.team_id = rec.partner_id.equipoventa_id

            return

    def _agrega_conceptos_viaje(self, id, preceiounitario):
        if preceiounitario <= 0:
            return []
        empresa = self.env["res.company"]._company_default_get("account.move")
        cfg = self.env["trafitec.parametros"].search([
            ("company_id", "=", empresa.id)
        ])
        conceptos = []
        impuestos = []

        for i in cfg.product.taxes_id:
            impuestos.append(i.id)

        flete = {
            "id": False,
            "move_id": id,
            "product_id": cfg.product_invoice.id,
            "name": cfg.product.name,
            "quantity": 1,
            "account_id": cfg.product_invoice.property_account_income_id.id,
            "uom_id": cfg.product_invoice.uom_id.id,
            "price_unit": preceiounitario,
            "discount": 0,
            "invoice_line_tax_ids": impuestos,
            "sistema": False
        }
        conceptos.append(flete)

        return conceptos

    def _agrega_conceptos_cargos_viajes(self, id):
        for rec in self:
            conceptos = []
            impuestos = []

            for v in rec.viajescp_id:
                cargos = rec.env["trafitec.viaje.cargos"].search(
                    [
                        ("line_cargo_id", "=", v.id),
                        ("tipo", "in", ("pagar_cr_cobrar_f", "pagar_cr_nocobrar_f")),
                        ("valor", ">", 0)
                    ]
                )
                for c in cargos:
                    for i in c.name.product_id.supplier_taxes_id:
                        impuestos.append(i.id)
                        product = c.name.product_id
                        cargo = {
                            "id": False,
                            "move_id": id,
                            "product_id": product.id,
                            "name": product.name,
                            "quantity": 1,
                            "account_id": (
                                product.property_account_expense_id.id
                            ),
                            "uom_id": c.name.product_id.uom_id.id,
                            "price_unit": c.valor,
                            "discount": 0,
                            "invoice_line_tax_ids": impuestos,
                            "sistema": False
                        }
                    conceptos.append(cargo)
            return conceptos

    def _agrega_conceptos_sistema(self):
        for rec in self:
            conceptos = []
            for invoice in rec.invoice_line_ids:
                if invoice.sistema:
                    concepto = {
                        "id": invoice.id,
                        "move_id": invoice.move_id.id,
                        "product_id": invoice.product_id.id,
                        "name": invoice.name,
                        "quantity": invoice.quantity,
                        "account_id": invoice.account_id.id,
                        "uom_id": invoice.uom_id.id,
                        "price_unit": invoice.price_unit,
                        "discount": invoice.discount,
                        "invoice_line_tax_ids": invoice.invoice_line_tax_ids,
                        "sistema": invoice.sistema
                    }
                    conceptos.append(concepto)
            return conceptos

    def _compute_folios_boletas(self):
        for rec in rec:
            folios = ""
            viajes_obj = rec.env["trafitec.viajes"]
            boletas_obj = rec.env["trafitec.viajes.boletas"]

            try:
                viajes_dat = viajes_obj.search([
                    ("factura_cliente_id", "=", rec.id)
                ])
                for v in viajes_dat:
                    boletas_dat = boletas_obj.search([
                        ("linea_id", "=", v.id)
                    ])
                    for b in boletas_dat:
                        folios += (b.name or "") + ", "
            except:
                rec.folios_boletas = folios

    @api.onchange("viajes_id")
    def _onchange_viajes(self):
        for rec in self:
            contiene = ""
            tons = 0
            productos = ""
            origenes = ""
            destinos = ""
            tarifa_ac = 0
            tarifa_an = 0
            origen_diferente = False
            origen_ac = ""
            origen_an = ""
            destino_diferente = False
            destino_ac = ""
            destino_an = ""
            producto_diferente = False
            producto_ac = ""
            producto_an = ""
            placas_diferente = False
            placas_ac = ""
            placas_an = ""
            placas = ""
            operadores_diferente = False
            operadores_ac = ""
            operadores_an = ""
            operadores = ""
            tarifas = ""
            c = 0
            
            if rec.tipo == "automatica":
                for v in rec.viajes_id:
                    c += 1
                    tarifa_ac = v.tarifa_cliente or 0
                    origen_ac = v.origen or ""
                    destino_ac = v.destino or ""
                    producto_ac = v.product.name or ""
                    operadores_ac = v.operador_id.name or ""
                    placas_ac = v.placas_id.license_plate or ""
                    if c == 1:
                        tarifa_an = tarifa_ac or 0
                        origen_an = origen_ac or ""
                        destino_an = destino_ac or ""
                        producto_an = producto_ac or ""
                        operadores_an = operadores_ac or ""
                        placas_an = placas_ac or ""
                    tarifas = "{:.2f}".format(tarifa_ac)
                    if tarifa_an != tarifa_ac:
                        tarifas = "Varias"
                    if origen_an != origen_ac:
                        origen_diferente = True
                    if destino_an != destino_ac:
                        destino_diferente = True
                    if producto_an != producto_ac:
                        producto_diferente = True
                    if operadores_an != operadores_ac:
                        operadores_diferente = True
                    if placas_an != placas_ac:
                        placas_diferente = True
                    origenes = v.origen.name
                    destinos = v.destino.name
                    placas = v.placas_id.license_plate or ""
                    operadores = v.operador_id.name or ""
                    productos = v.product.name
                    tons += (
                        v.peso_origen_remolque_1
                        + v.peso_origen_remolque_2
                    ) / 1000
                    tarifa_an = v.tarifa_cliente or 0
                    origen_an = v.origen or ""
                    destino_an = v.destino or ""
                    producto_an = v.product.name or ""
                    operadores_an = v.operador_id.name or ""
                    placas_an = v.placas_id.license_plate or ""
                if origen_diferente:
                    origenes = "Varios"
                if destino_diferente:
                    destinos = "Varios"
                if producto_diferente:
                    productos = "Varios"
                if operadores_diferente:
                    operadores = "Varios"
                if placas_diferente:
                    placas = "Varios"
                rec.origen = origenes
                rec.destino = destinos
                rec.operador_id = operadores
                rec.placas_id = placas
                if tons > 0:
                    contiene += (
                        "Flete con: {:.3f} toneladas del producto(s):".format(
                            tons
                        )
                        + " {}, con la tarifa: {}".format(
                            productos,
                            tarifas
                        )
                    )
                    rec.contiene = contiene
                conceptos = []
                viajes = []
                cargos = []
                sistema = []
                sistema = rec._agrega_conceptos_sistema()
                viajes = rec._agrega_conceptos_viaje(
                    rec._origin.id,
                    rec.total_fletes
                )
                cargos = rec._agrega_conceptos_cargos_viajes(rec._origin.id)
                rec.invoice_line_ids = []
                conceptos.extend(viajes)
                conceptos.extend(cargos)
                conceptos.extend(sistema)
                rec.invoice_line_ids = conceptos

            if rec.tipo == "manual" or rec.tipo == "automatica":

                if rec.viajes_id and len(rec.viajes_id) > 0:

                    try:
                        viaje1 = rec.viajes_id[0]
                        linea = viaje1.subpedido_id.linea_id
                        if linea.cotizacion_id.cliente_plazo_pago_id:
                            rec.payment_term_id = (
                                linea.cotizacion_id.cliente_plazo_pago_id.id
                            )
                    except:
                        pass

    @api.onchange("viajescp_id")
    def _onchange_viajescp(self):
        for rec in self:
            contiene = ""
            tons = 0
            productos = ""
            origenes = ""
            destinos = ""
            tarifa_ac = 0
            tarifa_an = 0
            origen_diferente = False
            origen_ac = ""
            origen_an = ""
            destino_diferente = False
            destino_ac = ""
            destino_an = ""
            producto_diferente = False
            producto_ac = ""
            producto_an = ""
            tarifas = ""
            c = 0
            if rec.es_cartaporte:
                for v in rec.viajescp_id:
                    c += 1
                    tarifa_ac = v.tarifa_cliente
                    origen_ac = v.origen
                    destino_ac = v.destino
                    producto_ac = v.product.name
                    if c == 1:
                        tarifa_an = tarifa_ac
                        origen_an = origen_ac
                        destino_an = destino_ac
                        producto_an = producto_ac
                    tarifas = "{:.2f}".format(tarifa_ac)
                    if tarifa_an != tarifa_ac:
                        tarifas = "Varias"
                    if origen_an != origen_ac:
                        origen_diferente = True
                    if destino_an != destino_ac:
                        destino_diferente = True
                    if producto_an != producto_ac:
                        producto_diferente = True
                    origenes = v.origen.name
                    destinos = v.destino.name
                    productos = v.product.name
                    tons += (
                        v.peso_origen_remolque_1
                        + v.peso_origen_remolque_2
                    ) / 1000
                    tarifa_an = v.tarifa_cliente
                    origen_an = v.origen
                    destino_an = v.destino
                    producto_an = v.product.name
                if origen_diferente:
                    origenes = "Varios"
                if destino_diferente:
                    destinos = "Varios"
                if producto_diferente:
                    productos = "Varios"
                rec.origen = origenes
                rec.destino = destinos
                conceptos = []
                sistema = rec._agrega_conceptos_sistema()
                viajes = rec._agrega_conceptos_viaje(
                    rec._origin.id,
                    rec.total_fletes
                )
                cargos = rec._agrega_conceptos_cargos_viajes(rec._origin.id)
                rec.invoice_line_ids = []
                conceptos.extend(cargos)
                conceptos.extend(sistema)
                rec.invoice_line_ids = conceptos

    @api.model
    def create(self, vals):
        cliente_obj = None
        cliente_dat = None
        if self._context.get("type", "out_invoice") == "out_invoice":
            cliente_obj = self.env["res.partner"]
            cliente_dat = cliente_obj.browse([vals.get("partner_id")])
            if cliente_dat:
                if cliente_dat.bloqueado_cliente_bloqueado:
                    raise UserError((
                        "El cliente esta bloqueado, motivo: "
                        + (
                            cliente_dat.bloqueado_cliente_clasificacion_id.name
                            or ""
                        )
                    ))
        factura = super(AccountMove, self).create(vals)
        return factura

    def obtener_viajes(self):
        for rec in self:
            lista = []
            if rec.id:
                sql = (
                    "select trafitec_viajes_id from account_invoice_trafitec"
                    + "_viajes_rel where account_move_id="
                    + str(rec.id)
                )
                rec.env.cr.execute(sql)
                viajessql = self.env.cr.fetchall()
                for v in viajessql:
                    id = v[0]
                    lista.append(id)
            return lista

    def viaje_facturado(self, id):
        viaje = self.env["trafitec.viajes"].search([("id", "=", id)])
        if viaje.en_factura:
            return False
        return True

    def write(self, vals):
        factura = None
        for invoice in self:
            antes = []
            despues = []
            if invoice.tipo == "manual" or invoice.tipo == "automatica":
                antes = invoice.obtener_viajes()
            factura = super(AccountMove, self).write(vals)
            if invoice.tipo == "manual" or invoice.tipo == "automatica":
                despues = invoice.obtener_viajes()
        return factura

    def action_invoice_open(self):
        for rec in self:
            error = False
            errores = ""
            cliente_nombre = ""
            cliente_saldo = 0
            cliente_limite_credito = 0
            prorroga_hay = False
            prorroga_fecha = None
            error = False
            errores = ""
            factura = self.env["account.move"].search([("id", "=", rec.id)])
            if rec.es_cartaporte:
                if not rec.viajescp_id:
                    raise ValidationError(
                        "Debe seleccionar al menos un viaje relacionado con "
                        + "la carta porte."
                    )
                for v in rec.viajescp_id:
                    vobj = self.env["trafitec.viajes"].search([
                        ("id", "=", v.id)
                    ])
                    if v.asociado_id.id != rec.partner_id.id:
                        error = True
                        errores += (
                            "El asociado del viaje "
                            + (str(v.name))
                            + " debe ser igual al de la factura.\r\n"
                        )
                    if v.flete_asociado <= 0:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " deben tener el flete del asociado calculado."
                            + "\r\n"
                        )
                    if v.documentacion_completa:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " deben tener documentación completa.\r\n"
                        )
                    if v.en_cp:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " ya tiene carta porte relacionada.\r\n"
                        )
            if rec.tipo == "automatica" or rec.tipo == "manual":
                if not rec.lineanegocio:
                    error = True
                    errores += "Debe especificar la línea de negocio.\r\n"
                if rec.tipo == "automatica":
                    if not rec.viajes_id:
                        error = True
                        errores += (
                            "Debe especificar al menos un viaje relacionado "
                            + "con la factura de cliente.\r\n"
                        )
                    totalflete = 0
                    for v in rec.viajes_id:
                        totalflete += v.flete_cliente
                    totalconceptos = 0
                    for invoice in rec.invoice_line_ids:
                        totalconceptos += invoice.price_subtotal
                    if totalflete <= 0:
                        error = True
                        errores += (
                            "El total de flete de viajes debe ser mayor a "
                            + "cero.\r\n"
                        )
                    if totalconceptos <= 0:
                        error = True
                        errores += (
                            "El total de flete de los conceptos debe ser "
                            + "mayor a cero.\r\n"
                        )
                for v in rec.viajes_id:
                    vobj = self.env["trafitec.viajes"].search([
                        ("id", "=", v.id)
                    ])
                    if v.cliente_id.id != rec.partner_id.id:
                        error = True
                        errores += (
                            "El cliente del viaje "
                            + (str(v.name))
                            + " debe ser igual al de la factura.\r\n"
                        )
                    if v.flete_cliente <= 0:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " debe tener el flete del cliente calculado."
                            + "\r\n"
                        )
                    if v.documentacion_completa:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " debe tener documentación completa.\r\n"
                        )
                    if v.en_factura:
                        error = True
                        errores += (
                            "El viaje "
                            + (str(v.name))
                            + " ya esta relacionado con una factura.\r\n"
                        )
            if error:
                raise ValidationError(("Alerta..\n" + errores))
            persona = rec.env["res.partner"]
            saldo = rec.partner_id.balance_invoices + rec.amount_total
            saldo_restante = rec.partner_id.limit_credit - saldo
            rec.partner_id.write(
                {
                    "balance_invoices": saldo,
                    "limit_credit_fletex": saldo_restante
                }
            )
            try:
                cliente_nombre = rec.partner_id.name
                cliente_saldo = persona.cliente_saldo_total(
                    rec.partner_id.id
                ) + rec.amount_total
                cliente_limite_credito = rec.partner_id.limite_credito
                prorroga_hay = rec.partner_id.prorroga
                if rec.partner_id.fecha_prorroga:
                    prorroga_fecha = datetime.datetime.strptime(
                        rec.partner_id.fecha_prorroga, "%Y-%m-%d").date()
                if rec.type == "out_invoice" and rec._context.get(
                    "validar_credito_cliente", True
                ) and prorroga_hay:
                    if cliente_saldo > cliente_limite_credito:
                        if (
                            prorroga_fecha
                            and datetime.date.today() > prorroga_fecha
                        ):
                            error = True
                            errores += (
                                "El cliente {} con saldo {:20,.2f} ha".format(
                                    cliente_nombre,
                                    cliente_saldo
                                )
                                + " excedido su crédito {:20,.2f} por".format(
                                    cliente_limite_credito
                                )
                                + " {:20,.2f} (Con prorroga).".format(
                                    cliente_saldo
                                    - cliente_limite_credito
                                )
                            )
                    else:
                        error = True
                        errores += (
                            "El cliente {} con saldo {:20,.2f} ha ".format(
                                cliente_nombre,
                                cliente_saldo
                            )
                            + "excedido su crédito {:20,.2f} por ".format(
                                cliente_limite_credito
                            )
                            + "{:20,.2f} (Sin prorroga).".format(
                                cliente_saldo
                                - cliente_limite_credito
                            )
                        )
            except:
                if self._context.get("type", "out_invoice") == "out_invoice":
                    for v in rec.viajes_id:
                        vobj = self.env["trafitec.viajes"].search([
                            ("id", "=", v.id)
                        ])
                        if vobj.en_factura:
                            error = True
                            errores += (
                                "El viaje {} ya tiene factura cliente".format(
                                    v.name
                                )
                                + ": {}.\r\n".format(
                                    (
                                        v.factura_cliente_id.name
                                        or v.factura_cliente_id.name
                                        or ""
                                    )
                                )
                            )
                else:
                    for vcp in rec.viajescp_id:
                        vobj = self.env["trafitec.viajes"].search([
                            ("id", "=", vcp.id)
                        ])
                        if vobj.en_cp:
                            error = True
                            errores += (
                                "El viaje {} ya tiene carta porte".format(
                                    vcp.name
                                )
                                + ": {}.\r\n".format(
                                    (
                                        vcp.factura_proveedor_id.name
                                        or vcp.factura_proveedor_id.name
                                        or ""
                                    )
                                )
                            )
            if error:
                raise ValidationError((errores))
            if self._context.get("type", "out_invoice") == "out_invoice":
                for v in rec.viajes_id:
                    v.with_context(validar_credito_cliente=False).write({
                        "en_factura": True,
                        "factura_cliente_id": rec.id
                    })
            else:
                for v in rec.viajescp_id:
                    v.with_context(validar_credito_cliente=False).write({
                        "en_cp": True,
                        "factura_proveedor_id": rec.id
                    })
            factura = super(AccountMove, self).action_invoice_open()
            return factura

    def action_invoice_cancel(self):
        if self._context.get("type", "out_invoice") == "out_invoice":
            view_id = self.env.ref(
                "sli_trafitec.sli_trafitec_facturas_cancelar"
            ).id
            return {
                "name": ("Cancelar factura de cliente"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "trafitec.facturas.cancelar",
                "views": [(view_id, "form")],
                "view_id": view_id,
                "target": "new",
                "context": {
                    "default_factura_id": self.id
                }
            }
        else:
            for f in self:
                f.factura_encontrarecibo = False
                f.contrarecibo_id = False
                if f.viajescp_id:
                    for v in f.viajescp_id:
                        v.with_context(validar_credito_cliente=False).write({
                            "en_cp": False,
                            "factura_proveedor_id": False
                        })
                    f.viajescp_id = [(5, 0, 0)]
            factura = super(AccountMove, self).action_invoice_cancel()
            return factura

    def action_liberar_viajes(self):
        self.ensure_one()
        if self.tipo != "manual":
            raise UserError(("La factura debe ser manual."))
        for v in self.viajes_id:
            if v.factura_cliente_id.id == self.id:
                v.with_context(validar_credito_cliente=False).write({
                    "factura_cliente_id": False,
                    "en_factura": False
                })

    def action_relacionar_viajes(self):
        self.ensure_one()
        if self.tipo != "manual":
            raise UserError(("La factura debe ser manual."))
        for v in self.viajes_id:
            if v.factura_cliente_id.id:
                v.with_context(validar_credito_cliente=False).write({
                    "factura_cliente_id": self.id,
                    "en_factura": True
                })

    def action_liberar_viajescp(self):
        for f in self:
            viajes = self.env["trafitec.viajes"].search([
                ("factura_proveedor_id", "=", f.id)
            ])
            if len(viajes) <= 0:
                raise UserError(("No se encontraron viajes relacionados."))
            for v in viajes:
                v.with_context(validar_credito_cliente=False).write({
                    "factura_proveedor_id": False,
                    "en_cp": False
                })

    def action_invoice_draft(self):
        factura = super(AccountMove, self).action_invoice_draft()

        return factura
