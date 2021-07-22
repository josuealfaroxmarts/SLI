## -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)


class trafitec_facturas_automaticas(models.Model):
    _name = 'trafitec.facturas.automaticas'
    _description ='trafitec facturas automaticas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Folio',default='Nuevo')
    cliente_id = fields.Many2one('res.partner', string="Cliente", domain="[('customer','=',True), ('parent_id', '=', False)]", required=True)
    currency_id = fields.Many2one("res.currency", string="Moneda", required=True)
    lineanegocio = fields.Many2one('trafitec.lineanegocio', string='Linea de negocios', required=True)
    csf = fields.Boolean(string='CSF', default=False)
    company_id = fields.Many2one('res.company', 'Company',
                                    default=lambda self: self.env['res.company']._company_default_get(
                                        'trafitec.facturas.automaticas'))
    viaje_id = fields.Many2many('trafitec.viajes', 'facturas_viaje_relation', 'facturas_id', 'viajes_id',
                                string='Viajes',
                                domain="[('cliente_id','=',cliente_id),('lineanegocio','=',lineanegocio),('state','=','Nueva'),('tipo_viaje','=','Normal'),('en_factura','=',False)]")
    payment_term_id = fields.Many2one('account.payment.term', string='Forma de pago', required=True)
    metodo_pago_id = fields.Many2one('l10n_mx_edi.payment.method', 'Metodo de Pago', help='Metodo de Pago Requerido por el SAT',
                                        required=True)
    uso_cfdi_id = fields.Many2one('sat.uso.cfdi', 'Uso CFDI', required=True, help='Define el motivo de la compra.')
    cargo_id = fields.One2many('trafitec.fact.aut.cargo', 'line_cargo_id')
    state = fields.Selection([('Nueva', 'Nueva'), ('Validada', 'Validada'),
                                ('Cancelada', 'Cancelada')], string='Estado',
                                default='Nueva')
    invoice_id = fields.Many2one('account.move', string='Factura cliente',
                                    domain="[('type','=','out_invoice'),('partner_id','=',cliente_id)]")

    
    def unlink(self):
        for reg in self:
            if reg.state == 'Validada':
                raise UserError(_(
                    'Aviso !\nNo se puede eliminar la factura automatica ({}) si esta validada.'.format(reg.name)))
        return super(trafitec_facturas_automaticas, self).unlink()


    @api.onchange('cliente_id')
    def _onchange_partner_trafitec(self):
        if self.cliente_id:
            self.cliente_origen_id = self.cliente_id
            self.domicilio_origen_id = self.cliente_id
            self.cliente_destino_id = self.cliente_id
            self.domicilio_destino_id = self.cliente_id

    def _get_parameter_company(self,vals):
        if vals.company_id.id != False:
            company_id = vals.company_id
        else:
            company_id = self.env['res.company']._company_default_get('trafitec.contrarecibo')
        parametros_obj = self.env['trafitec.parametros'].search([('company_id', '=', company_id.id)])
        if len(parametros_obj) == 0:
            raise UserError(_(
                'Aviso !\nNo se ha creado ningun parametro para la compañia {}'.format(company_id.name)))
        return parametros_obj

    @api.onchange('csf','cliente_id','currency_id','lineanegocio')
    def _onchange_csf(self):
        if self.csf == True:
            return {
                'domain': {
                    'viaje_id': [('cliente_id','=',self.cliente_id.id),('moneda','=',self.currency_id.id),('lineanegocio','=',self.lineanegocio.id),('state','=','Nueva'),('tipo_viaje','=','Normal'),('csf','=',True),('en_factura','=',False)]
                }
            }
        else:
            return {
                'domain': {
                    'viaje_id': [('cliente_id', '=', self.cliente_id.id), ('moneda', '=', self.currency_id.id),
                                    ('lineanegocio', '=', self.lineanegocio.id), ('state', '=', 'Nueva'),
                                    ('tipo_viaje', '=', 'Normal'),('en_factura','=',False)]
                }
            }

    @api.onchange('viaje_id')
    def _onchange_viaje_id(self):
        if self.viaje_id:
            r = []
            for viaje in self.viaje_id:
                if len(viaje.cargo_id) > 0:
                    for cargos in viaje.cargo_id:
                        apagador = False
                        for rr in r:
                            if rr.get('name') == cargos.name:
                                apagador = True
                                rr['valor'] = rr.get('valor') + cargos.valor
                        if apagador == False:
                            value = {
                                'name' : cargos.name,
                                'valor' : cargos.valor
                            }
                            r.append(value)
            self.cargo_id = r

    @api.onchange('cargo_id')
    def _onchange_subtotal_g(self):
        if self.viaje_id:
            amount = 0
            for viaje in self.viaje_id:
                amount += viaje.flete_cliente
            for cargo in self.cargo_id:
                amount += cargo.valor
            self.subtotal_g = amount
        else:
            self.subtotal_g = 0

    
    def _compute_subtotal(self):
        if self.viaje_id:
            amount = 0
            for viaje in self.viaje_id:
                amount += viaje.flete_cliente
            for cargo in self.cargo_id:
                amount += cargo.valor
            self.subtotal_g = amount
        else:
            self.subtotal_g = 0

    subtotal_g = fields.Monetary(string='Subtotal', compute='_compute_subtotal')

    @api.onchange('subtotal_g')
    def _onchange_iva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.subtotal_g:
            self.iva_g = self.subtotal_g * (parametros_obj.iva.amount / 100)
        else:
            self.iva_g = 0

    
    def _compute_iva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.subtotal_g:
            self.iva_g = self.subtotal_g * (parametros_obj.iva.amount / 100)
        else:
            self.iva_g = 0

    iva_g = fields.Monetary(string='Iva', compute='_compute_iva')

    @api.onchange('subtotal_g')
    def _onchange_riva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.subtotal_g:
            self.r_iva_g = (self.subtotal_g * (parametros_obj.retencion.amount / 100))
        else:
            self.r_iva_g = 0

    
    def _compute_riva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.subtotal_g:
            self.r_iva_g = (self.subtotal_g * (parametros_obj.retencion.amount / 100))
        else:
            self.r_iva_g = 0

    r_iva_g = fields.Monetary(string='R. IVA', compute='_compute_riva')

    @api.onchange('subtotal_g', 'iva_g', 'r_iva_g')
    def _onchange_total(self):
        self.total_g = self.subtotal_g + self.iva_g + self.r_iva_g

    
    def _compute_total(self):
        self.total_g = self.subtotal_g + self.iva_g + self.r_iva_g

    total_g = fields.Monetary(string='Total', compute='_compute_total')


    
    def action_available(self):
        if self.invoice_id.id == False:
            parametros_obj = self._get_parameter_company(self)
            print("**************Parametros:"+str(parametros_obj))
            valores = {
                'type': 'out_invoice',
                'date': datetime.datetime.now(),
                'partner_id': self.cliente_id.id,
                'partner_shipping_id': self.domicilio_origen_id.id,
                'metodo_pago_id': self.metodo_pago_id.id,
                'payment_term_id': self.payment_term_id.id,
                'uso_cfdi_id' : self.uso_cfdi_id.id,
                'journal_id': parametros_obj.journal_id_invoice.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'account_id': parametros_obj.account_id_invoice.id,
                'ref': 'Factura generada automaticamente.'
            }
            print("X**************Valores:" + str(valores))
            invoice_id = self.env['account.move'].create(valores)

            amount = 0
            for viaje in self.viaje_id:
                amount += viaje.flete_cliente

            inv_line = {
                'invoice_id': invoice_id.id,
                'product_id': parametros_obj.product_invoice.id,
                'name': parametros_obj.product_invoice.name,
                'quantity': 1,
                'account_id': parametros_obj.account_id_invoice.id,
                # order.lines[0].product_id.property_account_income_id.id or order.lines[0].product_id.categ_id.property_account_income_categ_id.id,
                'uom_id': parametros_obj.product_invoice.product_tmpl_id.uom_id.id,
                'price_unit': amount,
                'discount': 0
            }
            print("**************Valores Linea:" + str(inv_line))
            self.env['account.move.line'].create(inv_line)

            for cargo in self.cargo_id:
                inv_line = {
                    'invoice_id': invoice_id.id,
                    'product_id': cargo.name.product_id.id,
                    'name': cargo.name.product_id.name,
                    'quantity': 1,
                    'account_id': parametros_obj.account_id_invoice.id,
                    # order.lines[0].product_id.property_account_income_id.id or order.lines[0].product_id.categ_id.property_account_income_categ_id.id,
                    'uom_id': cargo.name.product_id.product_tmpl_id.uom_id.id,
                    'price_unit': cargo.valor,
                    'discount': 0
                }
                self.env['account.move.line'].create(inv_line)

            account_tax_obj = self.env['account.account'].search([('name', '=', 'IVA Retenido Efectivamente Cobrado')])

            if account_tax_obj:
                inv_tax = {
                    'invoice_id': invoice_id.id,
                    'name': 'Impuestos',
                    'account_id': account_tax_obj.id,
                    'amount': self.iva_g + self.r_iva_g,
                    'sequence': '0'
                }
                print("**************Valores Tax:" + str(inv_tax))
                self.env['account.move.tax'].create(inv_tax)

            self.invoice_id = invoice_id

            for viaje in self.viaje_id:
                viaje.write({'en_factura':True})

            self.write({'state': 'Validada'})


    
    def action_cancel(self):
        for viaje in self.viaje_id:
            viaje.write({'en_factura': False})
        self.write({'state': 'Cancelada'})

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Factura.Automatica') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Factura.Automatica') or _('Nuevo')

        return super(trafitec_facturas_automaticas, self).create(vals)

    #Otros
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    cliente_origen_id = fields.Many2one('res.partner', string="Cliente origen", domain="[('customer','=',True), ('parent_id', '=', False)]",required=True)
    domicilio_origen_id = fields.Many2one('res.partner', string="Domicilio origen", domain="['|',('parent_id', '=', cliente_origen_id),('id','=',cliente_origen_id)]",required=True)
    cliente_destino_id = fields.Many2one('res.partner', string="Cliente destino", domain="[('customer','=',True), ('parent_id', '=', False)]",required=True)
    domicilio_destino_id = fields.Many2one('res.partner', string="Domicilio destino",
                                            domain="['|',('parent_id', '=', cliente_destino_id),('id','=',cliente_destino_id)]",required=True)
    usar_origen_destino = fields.Boolean(string='Usar origen y destino del viaje',default=False)

    #contiene
    contiene = fields.Text(string='Contiene')
    observaciones = fields.Text(string='Observaciones')


class trafitec_fact_aut_cargo(models.Model):
    _name = 'trafitec.fact.aut.cargo'
    _description ='factura aut cargo'

    name = fields.Many2one('trafitec.tipocargosadicionales', string='Producto', required=True, readonly=True)
    valor = fields.Float(string='Total', required=True, readonly=True)
    line_cargo_id = fields.Many2one('trafitec.facturas.automaticas', string='Id factura automatica')
