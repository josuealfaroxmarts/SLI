## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class trafitec_cargos(models.Model):
    _name = 'trafitec.cargos'
    _order= 'id desc'

    viaje_id = fields.Many2one('trafitec.viajes', string='Viajes ID', ondelete='cascade',readonly=False)
    monto = fields.Float(string='Monto',readonly=False)
    tipo_cargo = fields.Selection(string="Tipo de cargo", selection=[('comision', 'comision'), ('merma', 'merma'), ('descuentos', 'descuentos')] )
    asociado_id = fields.Many2one('res.partner', domain="[('asociado','=',True)]", string="Asociado", required=True,readonly=False)
    descuento_id = fields.Many2one('trafitec.descuentos', string='ID descuentos', ondelete='cascade')
    abono_id = fields.One2many('trafitec.comisiones.abono', 'abonos_id')
    valor = fields.Char(string='valor')

    
    def unlink(self):
        if len(self)>1:
            raise UserError(_(
                'Alerta..\nNo se puede eliminar mas de una comisión a la vez.'))
        if self.tipo_cargo == 'comision':
            if self.viaje_id.id != False:
                raise UserError(_(
                    'Aviso !\nNo se puede eliminar una comision que tenga viajes.'))
            if self.abonado > 0:
                raise UserError(_(
                    'Aviso !\nNo se puede eliminar una comision que tenga abonos.'))
        return super(trafitec_cargos, self).unlink()

    
    def name_get(self):
        result = []
        name=""
        for rec in self:
            if rec.id:
                name = str(rec.id)+' '
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    
    @api.depends('abono_id.name')
    def _compute_abonado(self):
        self.abonado = sum(line.name for line in self.abono_id)

    abonado = fields.Float(compute='_compute_abonado',string='Abonado',store=True)

    
    @api.depends('abono_id','monto','abonado')
    def _compute_saldo(self):
        #if self.tipo_cargo == 'comision':
        #    if self.abonado:
                self.saldo = self.monto - self.abonado
        #    else:
        #        self.saldo = self.monto

    saldo = fields.Float(compute='_compute_saldo',string='Saldo',store=True)


class trafitec_abonos(models.Model):
    _name = 'trafitec.abonos'

    cargo_id = fields.Integer(string='Id del padre')
    monto = fields.Float(string='monto')
    detalle = fields.Text(string='detalle')
    cobradoen = fields.Char(string='Cobrado en')
    descuento_abono_id = fields.Many2one('trafitec.descuentos.abono',string='Id del abono a descuento')
    comision_abono_id = fields.Many2one('trafitec.comisiones.abono', string='Id del abono a comision')


#Descuentos.
class trafitec_descuentos(models.Model):
    _name = 'trafitec.descuentos'
    _order = 'id desc'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'id'

    name = fields.Char(string="Folio")
    viaje_id = fields.Many2one('trafitec.viajes', string="Viaje", track_visibility='onchange')
    flete_asociado = fields.Float(string='Flete asociado', related='viaje_id.flete_asociado', readonly=True)
    asociado_id = fields.Many2one('res.partner', string="Asociado", domain="[('asociado','=',True)]", required=True)
    operador_id = fields.Many2one('res.partner', string="Operador", domain="[('operador','=',True)]")
    concepto = fields.Many2one('trafitec.concepto.anticipo', string="Concepto", required=True)
    monto = fields.Float(string="Monto", required=True, track_visibility='onchange')
    proveedor = fields.Many2one('res.partner', string="Proveedor", domain="[('supplier','=',True)]", track_visibility='onchange')
    cobro_fijo = fields.Boolean(string='Cobro fijo', track_visibility='onchange')
    monto_cobro = fields.Float(string='Cantidad', track_visibility='onchange')
    folio_nota = fields.Char(string='Folio nota', track_visibility='onchange')
    comentarios = fields.Text(string='Comentarios', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'trafitec.descuentos'), track_visibility='onchange')
    abono_id = fields.One2many('trafitec.descuentos.abono','abonos_id', track_visibility='onchange')
    fecha = fields.Date(string='Fecha', readonly=True, index=True, copy=False,
                              default=fields.Datetime.now, track_visibility='onchange')

    @api.depends('es_combustible_litros', 'es_combustible_costoxlt')
    def compute_es_combustible_total(self):
        self.es_combustible_total = self.es_combustible_litros*self.es_combustible_costoxlt

    @api.depends('es_combustible_total', 'es_combustible_pcomision')
    def compute_es_combustible_comision(self):
        self.es_combustible_comision = self.es_combustible_total*(self.es_combustible_pcomision/100)

    @api.depends('es_combustible_total', 'es_combustible_comision')
    def compute_es_combustible_totalcomision(self):
        self.es_combustible_totalcomision = self.es_combustible_total+self.es_combustible_comision


    #state = fields.Selection(string="Estado", selection=[('cancelado', 'Cancelado'), ('activo', 'Activo')], default='activo', track_visibility='onchange')
    state = fields.Selection(string='Estado', selection=[('borrador', 'Borrador'), ('activo', 'Aprobado'), ('cancelado', 'Cancelado')], default='borrador', track_visibility='onchange')
    es_combustible = fields.Boolean(string='Vale de combustible', default=False, track_visibility='onchange')
    es_combustible_litros = fields.Float(string='Litros', default=0, track_visibility='onchange')
    es_combustible_costoxlt = fields.Float(string='Costo por litro', default=0, track_visibility='onchange')
    es_combustible_total = fields.Float(string='Total', default=0, compute='compute_es_combustible_total', store=True, track_visibility='onchange', help='Total sin comisión.')
    
    es_combustible_pcomision = fields.Float(string='Porcentaje comisión (%)', default=0, track_visibility='onchange')
    es_combustible_comision = fields.Float(string='Comisión', default=0,
                                           compute='compute_es_combustible_comision',
                                           store=True,
                                           track_visibility='onchange')
    es_combustible_totalcomision = fields.Float(string='Total', default=0,
                                                compute='compute_es_combustible_totalcomision',
                                                store=True,
                                                track_visibility='onchange',
                                                help='Total con comisión.')


    
    def action_aprobar(self):
        self.ensure_one()
        error = False
        errores = ''

        if self.monto <= 0:
           error = True
           errores += 'Debe especificar el monto.\n'

        if not self.proveedor:
           error = True
           errores += 'Debe especificar el proveedor.\n'

        if not self.folio_nota:
           error = True
           errores += 'Debe especificar el folio de la nota.\n'

        if error:
            raise UserError(errores)

        self.state = 'activo'

    
    def action_borrador(self):
        self.ensure_one()
        self.state = 'borrador'

    
    @api.constrains('monto', 'abono_total')
    def _check_monto_abono(self):
        if self.monto and self.abono_total:
            if self.abono_total > self.monto:
                raise UserError(_('Aviso !\nEl abono del descuento ({}) debe ser manor o igual al saldo del descuento ({}).'.format(self.abono_total, self.monto)))

    
    def copy(self):
        raise UserError("No se permite duplicar descuentos.")

    
    def unlink(self):
        raise UserError("No se permite borrar descuentos.")

        if self.abono_total > 0:
            raise UserError(_('Aviso !\nNo se puede eliminar un descuento que tenga abonos.'))
        return super(trafitec_descuentos, self).unlink()

    
    @api.depends('abono_id.name')
    def _compute_abono_total(self):
        self.abono_total = sum(line.name for line in self.abono_id)

    abono_total = fields.Float(string='Abonos', compute='_compute_abono_total',store=True)

    
    @api.depends('abono_total', 'monto')
    def _compute_saldo(self):
        if self.abono_total:
            self.saldo = self.monto - self.abono_total
        else:
            self.saldo = self.monto

    saldo = fields.Float(string='Saldo', compute='_compute_saldo',store=True)

    @api.constrains('monto')
    def _check_monto(self):
        if self.monto <= 0:
            raise UserError(_(
                'Aviso !\nEl monto debe ser mayor a cero.'))

    @api.constrains('monto_cobro')
    def _check_monto_cobro(self):
        if self.cobro_fijo == True:
            if self.monto_cobro <= 0:
                raise UserError(_(
                    'Aviso !\nEl monto del cobro debe ser mayor a cero.'))


    @api.onchange('viaje_id')
    def _onchange_viaje(self):
        if self.viaje_id:
            self.asociado_id = self.viaje_id.asociado_id
            self.operador_id = self.viaje_id.operador_id

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Descuentos') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Descuentos') or _('Nuevo')

        v_id = super(trafitec_descuentos, self).create(vals)

        if 'viaje_id' in vals:
            valores = {'viaje_id': vals['viaje_id'], 'monto': vals['monto'], 'tipo_cargo': 'descuentos','asociado_id' : vals['asociado_id'], 'descuento_id' : v_id.id}
        else:
            valores = {'monto': vals['monto'], 'tipo_cargo': 'descuentos',
                       'asociado_id': vals['asociado_id'], 'descuento_id' : v_id.id}
        self.env['trafitec.cargos'].create(valores)
        return v_id

    
    def write(self, vals):
        if 'viaje_id' in vals:
            viaje_id = vals['viaje_id']
        else:
            if self.viaje_id:
                viaje_id = self.viaje_id.id
            else:
                viaje_id = None

        if 'monto' in vals:
            monto = vals['monto']
        else:
            monto = self.monto
        if 'asociado_id' in vals:
            asociado_id = vals['asociado_id']
        else:
            asociado_id = self.asociado_id.id

        valores = {'viaje_id': viaje_id, 'monto': monto, 'tipo_cargo': 'descuentos',
                   'asociado_id': asociado_id, 'descuento_id': self.id}

        obc_cargos = self.env['trafitec.cargos'].search(
            ['&', ('descuento_id', '=', self.id), ('tipo_cargo', '=', 'descuentos')])
        if len(obc_cargos) == 0:
            self.env['trafitec.cargos'].create(valores)
        else:
            obc_cargos.write(valores)

        return super(trafitec_descuentos, self).write(vals)

    
    """
    Cancela descuento verificando si tiene abonos.
    """
    
    def action_cancelar(self):
        for rec in self:
            abonos_obj = self.env['trafitec.descuentos.abono']
            #viajes_obj = self.env['trafitec.viajes']
            abonos_dat = abonos_obj.search([('abonos_id', '=', rec.id)])
            if abonos_dat and len(abonos_dat) > 0:
                raise UserError(_("Este descuento tiene abonos."))

            #Quita la realacion con el viaje.
            if rec.viaje_id:
                if rec.viaje_id.descuento_combustible_id.id == rec.id:
                    rec.viaje_id.with_context(validar_credito_cliente=False, validar_cliente_moroso=False).write({'descuento_combustible_id': False})
                    #rec.viaje_id.descuento_combustible_id = False

            #rec.abono_total = 0
            #rec.saldo = self.monto
            rec.state = 'cancelado'
        


class trafitec_descuentos_abono(models.Model):
    _name = 'trafitec.descuentos.abono'

    name = fields.Float(string='Abono', required=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Datetime.now)
    observaciones = fields.Text(string='Observaciones')
    tipo = fields.Selection([('manual','Manual'),('contrarecibo','Contra recibo')],string='Tipo', default='manual')
    abonos_id = fields.Many2one('trafitec.descuentos', ondelete='cascade')
    contrarecibo_id = fields.Many2one('trafitec.contrarecibo', ondelete='restrict')
    permitir_borrar = fields.Boolean(string='Permitir borrar', default=False)

    
    def unlink(self):
        #if self.tipo == 'contrarecibo':
        #    if self.permitir_borrar != False:
        #        raise UserError(_(
        #            'Aviso !\nNo se puede eleminar un abono de un contra recibo.'))
        #if self.tipo == 'manual':
        #obj = self.env['trafitec.con.descuentos'].search([('descuento_fk', '=', self.abonos_id.id), ('linea_id.state', '=', 'Nueva')])
        #for des in obj:
        #    res = des.saldo + self.name
        #    abonado = des.anticipo - res
        #    des.write({'saldo': res, 'abonos': abonado, 'abono': res})
        return super(trafitec_descuentos_abono, self).unlink()

    @api.constrains('name')
    def _check_abono(self):
        if self.name <= 0:
            raise UserError(_('Aviso !\nEl monto del abono debe ser mayor a cero.'))

    @api.constrains('name')
    def _check_monto_mayor(self):
        obj_abono = self.env['trafitec.descuentos.abono'].search([('abonos_id','=',self.abonos_id.id)])
        amount = 0
        for abono in obj_abono:
            amount += abono.name
        
        #if amount > self.abonos_id.monto:
        #   raise UserError(_('Aviso !\nEl monto de abonos ha sido superado al monto del descuento.'))


    @api.model
    def create(self, vals):
        id =  super(trafitec_descuentos_abono, self).create(vals)
        if 'tipo' in vals:
            tipo = vals['tipo']
        else:
            tipo = 'manual'
        valores = {
            'descuento_abono_id' : id.id,
            'monto': vals['name'],
            'detalle': vals['observaciones'],
            'cobradoen' : 'Descuento {}'.format(tipo)
        }
        self.env['trafitec.abonos'].create(valores)
        if tipo == 'manual':
            obj = self.env['trafitec.con.descuentos'].search([('descuento_fk','=',vals['abonos_id']),('linea_id.state','=','Nueva')])
            for des in obj:
                res = des.saldo - vals['name']
                abonado = des.anticipo - res
                des.write({'saldo':res, 'abonos': abonado, 'abono':res})
        return id

    
    def write(self, vals):
        if 'name' in vals:
            monto = vals['name']
        else:
            monto = self.name
        if 'observaciones' in vals:
            detalle = vals['observaciones']
        else:
            detalle = self.observaciones
        valores = {
            'monto': monto,
            'detalle': detalle
        }
        obj = self.env['trafitec.abonos'].search([('descuento_abono_id','=',self.id)])
        obj.write(valores)
        if self.tipo == 'manual' and 'name' in vals:
            obj = self.env['trafitec.con.descuentos'].search([('descuento_fk','=',self.abonos_id.id),('linea_id.state','=','Nueva')])
            for des in obj:
                if self.name > vals['name']:
                    res = des.saldo + (self.name - vals['name'])
                else:
                    res = des.saldo - (vals['name'] - self.name)
                if res == 0:
                    des.unlink()
                else:
                    abonado = des.anticipo - res
                    des.write({'saldo':res, 'abonos': abonado, 'abono':res})

        return super(trafitec_descuentos_abono, self).write(vals)

class trafitec_comisiones_abono(models.Model):
    _name = 'trafitec.comisiones.abono'

    name = fields.Float(string='Abono', required=True)
    fecha = fields.Date(string='Fecha', required=True, default=fields.Datetime.now)
    observaciones = fields.Text(string='Observaciones')
    tipo = fields.Selection([('manual','Manual'),('contrarecibo','Contra recibo')],string='Tipo', default='manual')
    abonos_id = fields.Many2one('trafitec.cargos', ondelete='cascade')
    contrarecibo_id = fields.Many2one('trafitec.contrarecibo', ondelete='restrict')
    permitir_borrar = fields.Boolean(string='Permitir borrar', default=False)

    
    def unlink(self):
        #if self.tipo == 'contrarecibo':
            #if self.permitir_borrar != False:
            #    raise UserError(_(
            #        'Aviso !\nNo se puede eleminar un abono de un contra recibo.'))

        if self.tipo == 'manual':
            obj = self.env['trafitec.con.comision'].search(
                [('cargo_id', '=', self.abonos_id.id), ('line_id.state', '=', 'Nueva')])
            for con in obj:
                res = con.saldo + self.name
                abonado = con.comision - res
                con.write({'saldo': res, 'abonos': abonado})
        return super(trafitec_comisiones_abono, self).unlink()

    @api.constrains('name')
    def _check_abono(self):
        if self.name <= 0:
            raise UserError(_(
                'Aviso !\nEl monto del abono debe ser mayor a cero.'))

    @api.constrains('name')
    def _check_monto_mayor(self):
        obj_abono = self.env['trafitec.comisiones.abono'].search([('abonos_id','=',self.abonos_id.id)])
        amount = 0
        for abono in obj_abono:
            amount += abono.name
        if amount > self.abonos_id.monto:
            raise UserError(_(
                'Aviso !\nEl monto de abonos ha sido superado al monto de la comision.'))


    @api.model
    def create(self, vals):
        id =  super(trafitec_comisiones_abono, self).create(vals)
        if 'tipo' in vals:
            tipo = vals['tipo']
        else:
            tipo = 'manual'
        valores = {
            'comision_abono_id' : id.id,
            'monto': vals['name'],
            'detalle': vals['observaciones'],
            'cobradoen' : 'Comision {}'.format(tipo)
        }
        self.env['trafitec.abonos'].create(valores)
        if tipo == 'manual':
            obj = self.env['trafitec.con.comision'].search([('cargo_id','=',vals['abonos_id']),('line_id.state','=','Nueva')])
            for con in obj:
                res = con.saldo - vals['name']
                abonado = con.comision - res
                con.write({'saldo':res, 'abonos': abonado})
        return id

    
    def write(self, vals):
        if 'name' in vals:
            monto = vals['name']
        else:
            monto = self.name
        if 'observaciones' in vals:
            detalle = vals['observaciones']
        else:
            detalle = self.observaciones
        valores = {
            'monto': monto,
            'detalle': detalle
        }
        obj = self.env['trafitec.abonos'].search([('comision_abono_id','=',self.id)])
        obj.write(valores)

        if self.tipo == 'manual' and 'name' in vals:
            obj = self.env['trafitec.con.comision'].search([('cargo_id','=',self.abonos_id.id),('line_id.state','=','Nueva')])
            for con in obj:
                if self.name > vals['name']:
                    res = con.saldo + (self.name - vals['name'])
                else:
                    res = con.saldo - (vals['name'] - self.name)
                abonado = con.comision - res
                con.write({'saldo': res, 'abonos': abonado})


        return super(trafitec_comisiones_abono, self).write(vals)