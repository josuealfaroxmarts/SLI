# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError


class TrafitecParametros(models.Model):
    _name = "trafitec.parametros"
    _description = "Parametros"

    name = fields.Char(
        string="Nombre",
        default="",
        required=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        default=lambda self: self.env["res.company"]._company_default_get(
            "trafitec.parametros"
        ),
        required=True
    )
    product = fields.Many2one(
        "trafitec.product.template",
        string="Producto",
        required=True
    )
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Forma de pago",
        required=True
    )
    iva = fields.Many2one(
        "account.tax",
        string="Porcentaje de IVA",
        required=True
    )
    retencion = fields.Many2one(
        "account.tax",
        string="Porcentaje de retencion",
        required=True
    )
    pronto_pago = fields.Float(
        string="Porcentaje pronto pago", 
        required=True
    )
    journal_id_invoice = fields.Many2one(
        "account.journal",
        string="Diario",
        required=True
    )
    account_id_invoice = fields.Many2one(
        "account.account",
        string="Planes contable",
        required=True
    )
    product_invoice = fields.Many2one(
        "product.product",
        string="Productos",
        required=True
    )
    cr_diario_id = fields.Many2one(
        comodel_name="account.journal",
        string="Diario contable",
        required=True
    )
    cr_plancontable_id = fields.Many2one(
        comodel_name="account.account",
        string="Plan contable",
        required=True
    )
    cr_moneda_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda predeterminada",
        required=True
    )
    cr_lineanegocio_id = fields.Many2one(
        comodel_name="trafitec.linea.negocio",
        string="Línea negocio predeterminada"
    )
    nca_diario_pagos_id = fields.Many2one(
        string="Diario para pago automatico:",
        comodel_name="account.journal",
        required=True
    )
    nca_diario_cobros_id = fields.Many2one(
        string="Diario para cobro automatico:",
        comodel_name="account.journal",
        required=True
    )
    metodo_pago_id = fields.Many2one(
        "l10n_mx_edi.payment.method",
        "Metodo de Pago",
        help="Metodo de Pago Requerido por el SAT",
        required=True
    )
    cot_producto_id = fields.Many2one(
        string="ID Producto",
        comodel_name="product.product",
        help=(
            "Producto que se utilizara para crear las ordenes de venta a "
            + "partir de la cotización de trafitec."
        )
    )
    cot_envio_avance_pruebas_st = fields.Boolean(
        string="Pruebas",
        default=True,
        help="Indica el estado de pruebas para envio de avance de cotización."
    )
    cot_envio_avance_pruebas_correo = fields.Char(
        string="Correo",
        default="",
        help="Correo al que se enviara el avance de cotización de pruebas."
    )
    seguro_cargo_adicional_id = fields.Many2one(
        string="Tipo de cargo adicional",
        comodel_name="trafitec.tipo.cargos.adicionales",
        help=(
            "El tipo de cargo adicional que se utilizara para el seguro de "
            + "carga."
        )
    )
    descuento_combustible_externo_id = fields.Many2one(
        string="Combustible externo",
        comodel_name="product.product",
        help=(
            "Proveedor externo: Producto donde se obtendra el costo del "
            + "combustible para los calculos."
        )
    )
    descuento_combustible_interno_id = fields.Many2one(
        string="Combustible interno",
        comodel_name="product.product",
        help=(
            "Autoconsumo: Producto donde se obtendra el costo del combustible"
            + " para los calculos."
        )
    )
    descuento_combustible_proveedor_id = fields.Many2one(
        string="Proveedor",
        comodel_name="res.partner",
        help="Proveedor predeterminado para vales de combustible."
    )
    descuento_concepto_id = fields.Many2one(
        string="Concepto",
        comodel_name="trafitec.concepto.anticipo",
        help="Concepto predeterminado al generar descuento en el viaje."
    )
    descuento_combustible_pfactor = fields.Float(
        string="Porcentaje factor (%)",
        default=40,
        help="Porcentaje del flete para calculo de vale de combustible."
    )
    descuento_combustible_pcomision = fields.Float(
        string="Porcentaje de comisión (%)",
        default=1,
        help="Porcentaje de comisión."
    )

    @api.constrains(
        "descuento_combustible_pfactor",
        "descuento_combustible_pcomision"
    )
    def validacion(self):
        for rec in self:
            if not (rec.descuento_combustible_pfactor in range(0, 100)):
                raise UserError("El factor debe estar entre 0 100 %.")
            if not (rec.descuento_combustible_pcomision in range(0, 100)):
                raise UserError(
                    "El porcentaje de comisión debe estar entre 0 100 %."
                )

    @api.model
    def create(self, vals):
        parametros_obj = self.env["trafitec.parametros"].search([
            ("company_id", "=", vals["company_id"])
        ])
        if (len(parametros_obj) > 0):
            raise UserError(_(
                "Aviso !\nNo puede crear 2 parametros para la misma compañia"
            ))
        return super(TrafitecParametros, self).create(vals)

    def write(self, vals):
        if "company_id" in vals:
            raise UserError(_("Aviso !\nNo puede cambiar la compañia"))
        return super(TrafitecParametros, self).write(vals)
