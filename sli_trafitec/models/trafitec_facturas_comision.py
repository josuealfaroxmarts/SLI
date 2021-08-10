from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime


class TrafitecFacturasComision(models.Model):
    _name = 'trafitec.facturas.comision'
    _description ='comision facturas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio',
        default='Nuevo'
    )
    company_id = fields.Many2one(
        'res.company', 
        'Company',
        default=lambda self: self.env['res.company']._company_default_get('trafitec.facturas.automaticas')
    )
    asociado_id = fields.Many2one(
        'res.partner', 
        string="Asociado", 
        domain=[('asociado','=',True)], 
        required=True
    )
    domicilio_id = fields.Many2one(
        'res.partner', 
        string="Domicilio",
        domain=['|',('parent_id', '=', asociado_id),('id','=',asociado_id)],
        required=True
    )
    product_invoice = fields.Many2one(
        'product.product', 
        string='Producto', 
        required=True
    )
    payment_term_id = fields.Many2one(
        'account.payment.term', 
        string='Forma de pago', 
        required=True
    )
    metodo_pago_id = fields.Many2one(
        'l10n_mx_edi.payment.method', 
        'Metodo de Pago', 
        help='Metodo de Pago Requerido por el SAT',
        required=True
    )
    uso_cfdi_id = fields.Many2one(
        'sat.uso.cfdi', 
        'Uso CFDI', 
        required=True, 
        help='Define el motivo de la compra.'
    )
    comision_id = fields.One2many(
        comodel_name="trafitec.fact.linea.comision", 
        inverse_name="line_id"
    )
    contiene = fields.Text(string='Contiene')
    observaciones = fields.Text(string='Observaciones')
    state = fields.Selection(
        [('Nueva', 'Nueva'), 
        ('Validada', 'Validada'),
        ('Cancelada', 'Cancelada')], 
        string='Estado',
        default='Nueva'
    )
    move_id = fields.Many2one(
        'account.move', 
        string='Factura cliente',
        domain=[('type','=','out_invoice'),('partner_id','=',asociado_id)]
    )
    currency_id = fields.Many2one(
        "res.currency", 
        string="Moneda", 
        default="_default_pesos"
    )
    subtotal_g = fields.Monetary(
        string='Subtotal', 
        default=0
    )
    iva_g = fields.Monetary(
        string='Iva', 
        default=0
    )
    r_iva_g = fields.Monetary(
        string='R. IVA', 
        default=0
    )
    total_g = fields.Monetary(
        string='Total', 
        default=0
    )

    def unlink(self):
        for reg in self:
            if reg.state == 'Validada':
                raise UserError((
                    'Aviso !\nNo se puede eliminar esta factura por comision ({}) si esta validada.'.format(reg.name)))
        return super(TrafitecFacturasComision, self).unlink()

    @api.model
    def _default_pesos(self):
        if self.company_id.id != False:
            company_id = self.company_id
        else:
            company_id = self.env['res.company']._company_default_get('trafitec.contrarecibo')
        return company_id.currency_id

    @api.depends('viaje_id')
    def _totales(self):

        flete = 0
        subtotal = 0
        iva = 0
        riva = 0
        total = 0

        for v in self.viaje_id:
            subtotal += v.flete_asociado
            flete += v.flete_asociado

        iva = subtotal * 0.16
        riva = flete * 0.04
        total = subtotal + iva - riva

        self.subtotal_g = subtotal
        self.iva_g = iva
        self.r_iva_g = riva
        self.total_g = total

    def _get_parameter_company(self, vals):
        if vals.company_id.id != False:
            company_id = vals.company_id
        else:
            company_id = self.env['res.company']._company_default_get('trafitec.contrarecibo')
        parametros_obj = self.env['trafitec.parametros'].search(
            [('company_id', '=', company_id.id)])
        if len(parametros_obj) == 0:
            raise UserError((
                'Aviso !\nNo se ha creado ningun parametro para la compañia {}.'.format(company_id.name)))
        return parametros_obj

    @api.onchange('asociado_id')
    def _asociado(self):
        if self.asociado_id:
            obj_comi = self.env['trafitec.cargos'].search(
                [('asociado_id', '=', self.asociado_id.id), 
                ('tipo_cargo', '=', 'comision')])
            r = []
            self.comision_id = r
            for comision in obj_comi:
                if comision.saldo > 0:
                    valores = {
                        'name': comision.viaje_id.name,
                        'fecha': comision.viaje_id.fecha_viaje,
                        'comision': comision.monto,
                        'abonos': comision.abonado,
                        'saldo': comision.saldo,
                        'asociado_id': comision.asociado_id,
                        'tipo_viaje': comision.viaje_id.tipo_viaje,
                        'cargo_id': comision,
                        'viaje_id': comision.viaje_id
                    }
                    r.append(valores)
            self.comision_id = r

    
    def action_available(self):
        if self.comision_id and self.move_id.id == False:
            for comisi in self.comision_id:
                self.env['trafitec.comisiones.abono'].create({
                    'name': comisi.saldo,
                    'fecha': datetime.datetime.now(),
                    'abonos_id': comisi.cargo_id.id,
                    'observaciones': 'Generada en la factura {}'.format(comisi.line_id.name),
                    'tipo': 'contrarecibo',
                    'permitir_borrar' : True
                })
            parametros_obj = self._get_parameter_company(self)

            valores = {
                'type': 'out_invoice',
                'date': datetime.datetime.now(),
                'partner_id': self.asociado_id.id,
                'partner_shipping_id': self.domicilio_id.id,
                'metodo_pago_id': self.metodo_pago_id.id,
                'payment_term_id': self.payment_term_id.id,
                'uso_cfdi_id': self.uso_cfdi_id.id,
                'journal_id': parametros_obj.journal_id_invoice.id,
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'account_id': parametros_obj.account_id_invoice.id,
                'ref': 'Factura de cobro por comision {}.'.format(self.name)
            }
            move_id = self.env['account.move'].create(valores)


            inv_line = {
                'move_id': move_id.id,
                'product_id': self.product_invoice.id,
                'name': self.product_invoice.name,
                'quantity': 1,
                'account_id': parametros_obj.account_id_invoice.id,
                'uom_id': self.product_invoice.product_tmpl_id.uom_id.id,
                'price_unit': self.subtotal_g,
                'discount': 0
            }
            self.env['account.move.line'].create(inv_line)

            account_tax_obj = self.env['account.account'].search(
                [('name', '=', 'IVA Retenido Efectivamente Cobrado')])

            inv_tax = {
                'move_id': move_id.id,
                'name': 'Impuestos',
                'account_id': account_tax_obj.id,
                'amount': self.iva_g - self.r_iva_g,
                'sequence': '0'
            }
            self.env['account.move.tax'].create(inv_tax)
            self.move_id = move_id
            self.write({'state': 'Validada'})

    
    def action_cancel(self):
        for comision in self.comision_id:
            obj = self.env['trafitec.comisiones.abono'].search(
                [('abonos_id','=',comision.cargo_id.id),
                ('observaciones','=','Generada en la factura {}'.format(comision.line_id.name))])
            obj.write({'permitir_borrar': False})
            obj.unlink()
        self.write({'state': 'Cancelada'})

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Factura.Comision') or ('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Factura.Comision') or ('Nuevo')

        return super(TrafitecFacturasComision, self).create(vals)
