from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from xml.dom import minidom


class TrafitecAgregarQuitar(models.Model):
    _name = 'trafitec.agregar.quitar'
    _description = 'facturas agregar quitar'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio',
        default='Nuevo'
    )
    factura_id = fields.Many2one(
        'account.move',
        string='Factura',
        domain=[
            ('es_facturamanual', '=', True),
            ('pagada', '=', False)
        ]
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        domain=[
            ('customer', '=', True),
            ('parent_id', '=', False)
        ],
        related='factura_id.partner_id',
        store=True
    )
    domicilio_id = fields.Many2one(
        'res.partner',
        string='Domicilio',
        domain=[
            '|', ('parent_id', '=', 'cliente_origen_id'),
            ('id', '=', 'cliente_origen_id')
        ],
        related='factura_id.partner_shipping_id',
        store=True
    )
    placas_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehiculo',
        domain=[
            '&', ('asociado_id', '!=', False),
            ('operador_id', '!=', False)
        ],
        store=True,
        readonly=True
    )
    operador_id = fields.Many2one(
        'res.partner',
        string='Operador',
        domain=[('operador', '=', True)],
        store=True,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        store=True,
        related='factura_id.currency_id',
        readonly=True
    )
    lineanegocio = fields.Many2one(
        'trafitec.lineanegocio',
        string='Linea de negocios',
        store=True,
        related='factura_id.lineanegocio',
        readonly=True
    )
    contiene = fields.Text(
        string='Contiene',
        store=True,
        related='factura_id.contiene',
        readonly=True
    )
    total = fields.Monetary(
        string='Total',
        store=True,
        related='factura_id.amount_total',
        readonly=True
    )
    fecha = fields.Date(
        string='Fecha',
        store=True,
        related='factura_id.date',
        readonly=True
    )
    state = fields.Selection([
            ('Nueva', 'Nueva'),
            ('Validada', 'Validada'),
            ('Cancelada', 'Cancelada')
        ],
        string='Estado',
        default='Nueva')
    viaje_id = fields.Many2many(
        'trafitec.viajes',
        'facturas_viaje',
        'facturas_id',
        'viajes_id',
        string='Viajes',
        domain=[
            ('cliente_id', '=', cliente_id),
            ('lineanegocio', '=', lineanegocio),
            ('state', '=', 'Nueva'),
            ('tipo_viaje', '=', 'Normal'),
            ('en_factura', '=', False),
            ('csf', '=', False)
        ]
    )
    viajes_cobrados_id = fields.Many2many(
        'trafitec.viajes',
        'facturas_cobrados_viaje',
        'facturas_id',
        'viajes_id',
        string='Viajes cobrados'
    )
    observaciones = fields.Text(string='Observaciones')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'trafitec.agregar.quitar')
    )
    move_id = fields.Many2one(
        'account.move',
        string='Factura excedente',
        readonly=True
    )
    abonado = fields.Float(
        string='Abonado',
        compute='_compute_abonado'
    )
    saldo = fields.Float(
        string='Saldo',
        compute='_compute_saldo'
    )
    fletes = fields.Monetary(
        string='Fletes',
        compute='_compute_fletes'
    )
    maniobras = fields.Monetary(
        string='Maniobras',
        compute='_compute_maniobras'
    )
    subtotal_g = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal'
    )
    iva_g = fields.Monetary(
        string='Iva',
        compute='_compute_iva'
    )
    r_iva_g = fields.Monetary(
        string='R. IVA',
        compute='_compute_riva'
    )
    total_g = fields.Monetary(
        string='Total ',
        compute='_compute_total'
    )

    def unlink(self):
        for reg in self:
            if reg.state == 'Validada':
                raise UserError((
                    'Aviso !\nNo se puede eliminar ({})'.format(reg.name)
                    + ' si esta validada.'
                ))
        return super(TrafitecAgregarQuitar, self).unlink()

    @api.onchange('move_id')
    def _onchange_abono(self):
        for rec in self:
            if rec.move_id:
                res = {'warning': {
                    'title': ('Advertencia'),
                    'message': ('Se ha generado una factura excedente.')
                }}
                return res

    def _get_parameter_company(self, vals):
        if vals.company_id.id:
            company_id = vals.company_id
        else:
            company_id = self.env['res.company']._company_default_get(
                'trafitec.contrarecibo'
            )
        parametros_obj = self.env['trafitec.parametros'].search([
            ('company_id', '=', company_id.id)
        ])
        if len(parametros_obj) == 0:
            raise UserError((
                'Aviso !\nNo se ha creado ningun parametro para la compañia '
                + '{}'.format(company_id.name)
            ))
        return parametros_obj

    @api.onchange('factura_id')
    def _onchange_viajes_cobrados(self):
        for rec in self:
            if rec.factura_id:
                obj = self.env['trafitec.agregar.quitar'].search([
                    ('factura_id', '=', rec.factura_id.id),
                    ('state', '=', 'Validada')
                ])
                r = []
                if len(obj) > 0:
                    rec.viajes_cobrados_id = obj.viaje_id

    @api.onchange('factura_id')
    def _onchange_abonado(self):
        for rec in self:
            if rec.factura_id:
                rec.abonado = rec.factura_id.abonado

    def _compute_abonado(self):
        for rec in self:
            if rec.factura_id:
                rec.abonado = rec.factura_id.abonado

    @api.onchange('factura_id')
    def _onchange_saldo(self):
        if self.factura_id:
            self.saldo = self.total - self.abonado

    
    def _compute_saldo(self):
        if self.factura_id:
            self.saldo = self.total - self.abonado

    @api.onchange('viaje_id')
    def _onchange_fletes(self):
        amount = 0
        for record in self.viaje_id:
            if amount == 0:
                amount = record.flete_cliente
            else:
                amount += record.flete_cliente
        self.fletes = amount

    
    def _compute_fletes(self):
        amount = 0
        for record in self.viaje_id:
            if amount == 0:
                amount = record.flete_cliente
            else:
                amount += record.flete_cliente
        self.fletes = amount

    def _generar_factura_excedente(self, vals, parametros_obj):
        fact = vals.factura_id
        valores = {
            'origin': vals.name,
            'type': fact.type,
            'date': datetime.datetime.now(),
            'partner_id': fact.partner_id.id,
            'journal_id': fact.journal_id.id,
            'company_id': fact.company_id.id,
            'currency_id': fact.currency_id.id,
            'account_id': fact.account_id.id,
            'ref': 'Factura generada por excedente en el folio {} '.format(vals.name)
        }
        move_id = vals.env['account.move'].create(valores)

        product = self.env['product.product'].search([
            ('product_tmpl_id','=',parametros_obj.product_invoice.id)])

        piva = (parametros_obj.iva.amount / 100)
        priva = (parametros_obj.retencion.amount / 100)

        monto = self.factura_id.abonado - self.total

        subtotal = monto / (1 + (piva - priva))
        iva = subtotal * piva
        riva = subtotal * priva
        total = subtotal + iva + riva

        inv_line = {
            'move_id': move_id.id,
            'product_id': product.id,
            'name': product.name,
            'quantity': 1,
            'account_id': fact.account_id.id,
            'uom_id': parametros_obj.product_invoice.uom_id.id,
            'price_unit': subtotal,
            'price_unit': subtotal,
            'discount': 0
        }
        vals.env['account.move.line'].create(inv_line)


        inv_tax = {
            'move_id': move_id.id,
            'name': parametros_obj.iva.name,
            'account_id': parametros_obj.iva.account_id.id,
            'amount': (iva - riva),
            'sequence': '0'
        }
        vals.env['account.move.tax'].create(inv_tax)

        inv_ret = {
            'move_id': move_id.id,
            'name': parametros_obj.retencion.name,
            'account_id': parametros_obj.retencion.account_id.id,
            'amount': riva,
            'sequence': '0'
        }
        vals.env['account.move.tax'].create(inv_ret)

        return move_id

    
    def action_available(self):
        apag = False
        if self.saldo > self.total_g:
            self.factura_id.write(
                {'abonado':(self.total_g + self.factura_id.abonado)})
        else:
            apag = True
            self.factura_id.write(
                {'pagada': True, 'abonado':(self.factura_id.abonado + self.total_g)})

        for viaje in self.viaje_id:
            viaje.write({'en_factura': True})
        self.write({'state': 'Validada'})

        if apag == True:
            action_ctx = dict(self.env.context)
            view_id = self.env.ref('sli_trafitec.msj_factura_form').id
            return {
                'name': ('Advertencia'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.agregar.quitar',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': self.ids[0],
                'context': action_ctx
            }

    def action_cancel(self):
        self.factura_id.write(
            {'pagada': False, 'abonado': (self.factura_id.abonado - self.total_g)})
        for viaje in self.viaje_id:
            viaje.write({'en_factura': False})
        self.write({'state': 'Cancelada'})
        
    @api.onchange('viaje_id')
    def _onchange_maniobras(self):
        amount = 0
        for record in self.viaje_id:
            if amount == 0:
                amount = record.maniobras
            else:
                amount += record.maniobras
        self.maniobras = amount

    
    def _compute_maniobras(self):
        amount = 0
        for record in self.viaje_id:
            if amount == 0:
                amount = record.maniobras
            else:
                amount += record.maniobras
        self.maniobras = amount

    # Totales
    @api.onchange('fletes', 'maniobras')
    def _onchange_subtotal(self):
        self.subtotal_g = self.fletes + self.maniobras

    
    def _compute_subtotal(self):
        self.subtotal_g = self.fletes + self.maniobras

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

    @api.onchange('fletes')
    def _onchange_riva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.fletes:
            self.r_iva_g = (self.fletes * (parametros_obj.retencion.amount / 100))
        else:
            self.r_iva_g = 0

    def _compute_riva(self):
        parametros_obj = self._get_parameter_company(self)
        if self.fletes:
            self.r_iva_g = (self.fletes * (parametros_obj.retencion.amount / 100))
        else:
            self.r_iva_g = 0

    @api.onchange('subtotal_g', 'iva_g', 'r_iva_g')
    def _onchange_total(self):
        self.total_g = self.subtotal_g + self.iva_g - self.r_iva_g

    
    def _compute_total(self):
        self.total_g = self.subtotal_g + self.iva_g - self.r_iva_g

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Agregar.Quitar') or ('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Agregar.Quitar') or ('Nuevo')

        return super(TrafitecAgregarQuitar, self).create(vals)
