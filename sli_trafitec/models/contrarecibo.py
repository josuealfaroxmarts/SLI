## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
import math

_logger = logging.getLogger(__name__)


class trafitec_contrarecibo(models.Model):
    _name = 'trafitec.contrarecibo'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'


    def totales(self):
        flete = 0
        seguro = 0
        maniobras = 0
        cargosadicionales = 0
        mermas = 0
        mermas_an = 0
        mermas_de = 0

        descuentos_viajes = 0
        descuentos = 0
        descuentos_an = 0
        descuentos_de = 0

        comisiones_viajes = 0
        comisiones = 0
        comisiones_an = 0
        comisiones_de = 0

        prontopago = 0
        prontopago_an = 0
        prontopago_de = 0

        subtotal = 0
        iva = 0
        riva = 0
        total = 0

        parametros_obj = self._get_parameter_company(self)


        #Viajes.
        for v in self.viaje_id:
            #Flete.
            flete += v.flete_asociado

            #Maniobras.
            maniobras += v.maniobras

            #Mermas.
            mermas += v.merma_cobrar_pesos
            
            if self.mermas_bol == False:
                mermas_an += v.merma_cobrar_pesos
                mermas_de = 0
            else:
                mermas_an = 0
                mermas_de += v.merma_cobrar_pesos

            if v.pronto_pago == True:
                prontopago += v.flete_asociado * (parametros_obj.pronto_pago / 100)

        #Cargos adicionales.
        for ca in self.cargosadicionales_id:
            cargosadicionales += ca.valor

        #Descuentos.
        for d in self.descuento_id:
            descuentos += d.abono
            if d.viaje_id in self.viaje_id:
                descuentos_viajes += d.abono

        if self.cobrar_descuentos == 'No cobrar':
            descuentos_an = 0
            descuentos_de = 0

        if self.cobrar_descuentos == 'Todos':
            if self.descuento_bol == False:
                descuentos_an = descuentos
                descuentos_de = 0
            else:
                descuentos_an = 0
                descuentos_de = descuentos

        if self.cobrar_descuentos == 'Viajes del contrarecibo':
            if self.descuento_bol == False:
                descuentos_an = descuentos_viajes
                descuentos_de = 0
            else:
                descuentos_an = 0
                descuentos_de = descuentos_viajes


        #Comisiones.
        for c in self.comision_id:
            comisiones += c.saldo
            if c.viaje_id in self.viaje_id:
                comisiones_viajes += c.saldo

        if self.cobrar_comisiones == 'No cobrar':
            comisiones_an = 0
            comisiones_de = 0

        if self.cobrar_comisiones == 'Todos los viajes':
            if self.comision_bol == False:
                comisiones_an = comisiones
                comisiones_de = 0
            else:
                comisiones_an = 0
                comisiones_de = comisiones

        if self.cobrar_comisiones == 'Viajes del contrarecibo':
            if self.comision_bol == False:
                comisiones_an = comisiones_viajes
                comisiones_de = 0
            else:
                comisiones_an = 0
                comisiones_de = comisiones_viajes

        #Pronto pago.
        if self.prontopago_bol == False:
            prontopago_an = prontopago
            prontopago_de = 0
        else:
            prontopago_an = 0
            prontopago_de = prontopago


        #Totales.
        subtotal = flete+seguro+maniobras+cargosadicionales-mermas_an-descuentos_an-comisiones_an-prontopago_an
        if self.iva_option == 'CIR' or self.iva_option == 'CISR':
            iva = subtotal*0.16
        if self.iva_option == 'CIR':
            riva = subtotal*0.04
        total = subtotal+iva-riva

        return {
            'flete': flete,
            'seguro': seguro,
            'maniobras': maniobras,
            
            'mermas': mermas,
            'mermas_an': mermas_an,
            'mermas_de': mermas_de,

            'descuentos': descuentos,
            'descuentos_an': descuentos_an,
            'descuentos_de': descuentos_de,

            'comisiones': comisiones,
            'comisiones_an': comisiones_an,
            'comisiones_de': comisiones_de,

            'prontopago': prontopago,
            'prontopago_an': prontopago_an,
            'prontopago_de': prontopago_de,

            'subtotal': subtotal,
            'iva': iva,
            'riva': riva,
            'total': total
        }

    @api.model
    def _predeterminados_moneda(self):
        emp = self.env['res.company']._company_default_get('sli_trafitec')
        #print("Empresa:"+str(emp))
        res = self.env['trafitec.parametros'].search([('company_id', '=', emp.id)])
        return res[0].cr_moneda_id or False

    @api.model
    def _predeterminados_lineanegocio(self):
        res = self.env['trafitec.parametros'].search([])
        return res[0].cr_lineanegocio_id or False



    def _factura_relacionada(self, crear, vals):
        condiciones=[]

        if 'invoice_id' in vals:
            if vals['invoice_id']:
                condiciones.append(('invoice_id', '=', vals['invoice_id']))
            else:
                return
        else:
            return

        if crear:
            print(">>>>>VALORES AL CREAR:"+str(vals)+" Context:"+str(self.env.context)+" Self:"+str(self))
            print("Al crear")
        else:
            #print(">>>>>VALORES AL ESCRIBIR:"+str(vals)+" Context:"+str(self.env.context)+" Self:"+str(self))
            condiciones.append(('id', '!=', self.id))

        contrarecibo=self.env['trafitec.contrarecibo'].search(condiciones)

        #print(">> Condiciones: "+str(condiciones))

        folios=''
        if contrarecibo:
            for cr in contrarecibo:
                folios += cr.name + ' '
            raise UserError(_('La carta porte ya esta en otro contra recibo ({}).'.format(folios)))

    def _validaobservacione(self):
        #if (self.observaciones.trim() or "")=="":
        return False




    #@api.onchange("viaje_id","lineanegocio","currency_id","asociado_id",'iva_option','cobrar_descuentos','cobrar_comisiones','descuento_id','comision_id')
    #def _alcambiar(self):
    #    self._totales()

    def _carga_cargospendientes(self):
        self.cargospendientes_id=[]
        cargosx=[]
        cargos=self.env['trafitec.cargospendientes']
        cargospendientes=self.env['trafitec.cargos'].search([('asociado_id','=',self.asociado_id.id),('tipo_cargo','=','descuentos')])
        #cargospendientes=self.env['trafitec.cargos'].search([('asociado_id','=',self.asociado_id.id),('saldo','>',0),('tipo_cargo','=','descuentos')])
        for c in cargospendientes:
            nuevo={
                'descuento_id':c.id,
                'total':c.monto,
                'abonos':c.abonado,
                'saldo':c.saldo,
                'detalles':c.descuento_id.concepto.name
            }
            cargosx.append(nuevo)
        self.cargospendientes_id=cargosx

    
    def write(self,vals):
        #print("*****AL ESCRIBIR****** self: "+str(self)+" vals: "+str(vals))
        self._factura_relacionada(False,vals)
        #print("*****AL ESCRIBIR****** self: "+str(self)+" vals: "+str(self.))
        cr= super(trafitec_contrarecibo, self).write(vals)
        return cr

    
    def unlink(self):
        print(dir(self))
        raise UserError(_('Alerta..\nNo esta permitido borrar contra recibos.'))
    
        for reg in self:
            if reg.state == 'Validada':
                raise UserError(_('Alerta..\nNo se puede eliminar si el contra recibo({}) esta validado.'.format(reg.name)))
        return super(trafitec_contrarecibo, self).unlink()

    @api.onchange('normal')
    def _onchange_tipo_normal_check(self):
        if self.normal == True and self.psf == True:
            self.psf = False

    @api.onchange('psf')
    def _onchange_tipo_psf_check(self):
        if self.normal == True and self.psf == True:
            self.normal = False

    def _crear_factura_proveedor(self, vals):
        self._validar_viajes_seleccionados(vals)
        journal_obj = vals.env['account.journal'].search([('name', '=', 'Proveedores Transportistas')])
        account_obj = vals.env['account.account'].search([('name', '=', 'Proveedores Transportistas')])
        
        valores = {
            'origin': vals.name,
            'type': 'in_invoice',
            'date_invoice': datetime.datetime.now(),
            'partner_id': vals.asociado_id.id,
            'journal_id': journal_obj.id,
            'company_id': vals.company_id.id,
            'currency_id': vals.currency_id.id,
            'account_id': account_obj.id,
            'reference': 'Factura generada del contra recibo {} '.format(vals.name)
        }
        invoice_id = vals.env['account.invoice'].create(valores)

        product_obj = vals.env['product.product'].search([('default_code', '=', 'ServFletGran')])

        inv_line = {
            'invoice_id': invoice_id.id,
            'product_id': product_obj.id,
            'name': 'Factura generada del contra recibo {} '.format(vals.name),
            'quantity': 1,
            'account_id': account_obj.id,
            # order.lines[0].product_id.property_account_income_id.id or order.lines[0].product_id.categ_id.property_account_income_categ_id.id,
            'uom_id': product_obj.product_tmpl_id.uom_id.id,
            'price_unit': vals.subtotal,
            'price_unit': vals.subtotal,
            'discount': 0
        }
        vals.env['account.invoice.line'].create(inv_line)

        account_tax_obj = vals.env['account.account'].search([('name', '=', 'IVA Retenido Efectivamente Cobrado')])

        inv_tax = {
            'invoice_id': invoice_id.id,
            'name': vals.iva_option,
            'account_id': account_tax_obj.id,
            'amount': vals.iva + vals.r_iva,
            'sequence': '0'
        }
        vals.env['account.invoice.tax'].create(inv_tax)

        self._cambiar_estado_viaje(vals)
        return invoice_id

    def _cambiar_estado_viaje(self, vals):
        for viaje  in vals.viaje_id:
            viaje.en_contrarecibo = True

    def _validar_viajes_seleccionados(self, vals):
        for viaje  in vals.viaje_id:
            if viaje.en_contrarecibo == True:
                raise UserError(
                    _('Error !\nEl viaje con el folio {} ya fue asignado en otro contra recibo.'.format(viaje.name)))


    def _cobrar_descuentos(self):
        #print("-.....Cobrar descuentos: "+str(self))
        if self.cobrar_descuentos:
            if self.cobrar_descuentos == 'Todos':
                for descuento in self.descuento_id:
                    #print("****XXX Desucento:"+str(descuento))
                    obj_descuento=self.env['trafitec.descuentos'].search([('id','=',descuento.descuento_fk.id)])

                    if descuento.abono>obj_descuento.saldo:
                        raise UserError(_('Error !\nEl abono del descuento ({}) es mayor al saldo del descuento ({}).'.format(descuento.abono,obj_descuento.saldo)))
                    if descuento.abono <= 0:
                        continue

                    nuevo={
                            'name':descuento.abono,
                            'fecha':datetime.datetime.now().date(),
                            'observaciones': 'Generada en el contra recibo {}'.format(descuento.linea_id.name),
                            'tipo':'contrarecibo',
                            'abonos_id' : descuento.descuento_fk.id,
                            'contrarecibo_id':self.id,
                            'permitir_borrar' : True
                        }
                    #print("---Nuevo: "+str(nuevo))
                    self.env['trafitec.descuentos.abono'].create(nuevo)


            if self.cobrar_descuentos == 'Viajes del contrarecibo':
                amount = 0
                for descuento in self.descuento_id:
                    if descuento.viaje_id in self.viaje_id:
                        obj_descuento = self.env['trafitec.descuentos'].search([('id', '=', descuento.descuento_fk.id)])
                        if descuento.abono > obj_descuento.saldo:
                            raise UserError(_('Error !\nEl abono del descuento ({}) es mayor al saldo del descuento ({}).'.format(descuento.saldo,obj_descuento.saldo)))
                        if descuento.abono <= 0:
                            continue
                            
                        nuevo={
                            'name': descuento.abono,
                            'fecha': datetime.datetime.now(),
                            'observaciones': 'Generada en el contra recibo {}'.format(descuento.linea_id.name),
                            'tipo': 'contrarecibo',
                            'abonos_id': descuento.descuento_fk.id,
                            'contrarecibo_id': self.id,
                            'permitir_borrar': True
                        }
                        #print("---Nuevo: " + str(nuevo))
                        self.env['trafitec.descuentos.abono'].create(nuevo)


    def _cobrar_comisiones(self):
        if self.cobrar_comisiones:
            if self.cobrar_comisiones == 'Todos los viajes':
                for comisi in self.comision_id:
                    obj_comisi = self.env['trafitec.cargos'].search([('id', '=', comisi.cargo_id.id)])
                    if obj_comisi.saldo!=comisi.saldo:
                        raise UserError(_('Error !\nEl abono de comisión ({}) es mayor al saldo de la comision ({}).'.format(comisi.saldo,obj_comisi.saldo)))

                    self.env['trafitec.comisiones.abono'].create({
                        'name' : comisi.saldo,
                        'fecha': datetime.datetime.now().date(),
                        'abonos_id' : comisi.cargo_id.id,
                        'observaciones' : 'Generada en el contra recibo {}'.format(comisi.line_id.name),
                        'tipo' : 'contrarecibo',
                        'contrarecibo_id': self.id,
                        'permitir_borrar' : True
                    })
            if self.cobrar_comisiones == 'Viajes del contrarecibo':
                for comisi in self.comision_id:
                    if comisi.viaje_id in self.viaje_id:
                        obj_comisi = self.env['trafitec.cargos'].search([('id', '=', comisi.cargo_id.id)])
                        if obj_comisi.saldo != comisi.saldo:
                            raise UserError(_('Error !\nEl abono de comisión ({}) es mayor al saldo de la comision ({}).'.format(comisi.saldo,obj_comisi.saldo)))

                        self.env['trafitec.comisiones.abono'].create({
                            'name' : comisi.saldo,
                            'fecha': datetime.datetime.now().date(),
                            'abonos_id' : comisi.cargo_id.id,
                            'observaciones' : 'Generada en el contra recibo {}'.format(comisi.line_id.name),
                            'tipo' : 'contrarecibo',
                            'contrarecibo_id': self.id,
                            'permitir_borrar': True
                        })

    def _aplicapago(self,diario_id,factura_id,abono,moneda_id,persona_id,tipo='supplier',subtipo='inbound'):
        #factura = self.env['account.invoice'].search([('id', '=', self.id)])
        if abono<=0:
            return

        metodo=2
        if subtipo=='inbound':
            metodo=1


        valores = {
            'journal_id': diario_id,  # Ok.
            'payment_method_id': metodo,  # account_payment_method 1=Manual inbound, 2=Manual outbound.
            'payment_date': datetime.datetime.now().date(),  # Ok.
            'communication': 'Pago desde codigo por:{} de tipo:{} '.format(str(abono), tipo),  # Ok.
            'invoice_ids': [(4, factura_id, None)],  # [(4, inv.id, None) for inv in self._get_invoices()],
            'payment_type': subtipo,  # inbound,outbound
            'amount': abono,  # Ok.
            'currency_id': moneda_id,  # Ok.           s
            'partner_id': persona_id,  # Ok.
            'partner_type': tipo,  # Ok. customer,supplier
        }


        #print("***Pago auto: "+str(valores))
        pago = self.env['account.payment'].create(valores)
        pago.post()

        # REgistros contables.
        """
        movimiento = [(0, factura_id, {
            'name': pago.move_name,  # a label so accountant can understand where this line come from
            'amount_currency': 0,
            'debit': abono,  # amount of debit
            'credit': 0,  # amount of credit
            'account_id': 1,  # account
            'date': datetime.datetime.now().today(),
            'partner_id': persona_id,  # partner if there is one
            'currency_id': moneda_id,
            'payment_id': pago.id,
            'invoice_id': factura_id
        }),
        (0, factura_id, {
            'name': pago.move_name,
            'amount_currency': 0,
            'debit': 0,
            'credit': abono,
            'account_id': 3,
            'analytic_account_id': False,
            'date': datetime.datetime.now().today(),
            'partner_id': persona_id,
            'currency_id': moneda_id,
            'payment_id': pago.id,
            'invoice_id': factura_id
        })
        ]

        registro = {

            'period_id': 7,  # Fiscal period
            'partner_id': persona_id,
            'journal_id': diario_id,  # journal ex: sale journal, cash journal, bank journal....
            'date': datetime.datetime.now().date(),
            'ref': 'Por sistema compa:' + str(abono),
            'state': 'draft',
            'line_ids': movimiento,  # this is one2many field to account.move.line
        }


        id=False
        for mx in pago.move_line_ids:
            id=mx.move_id.id

        m1={
            'name': pago.move_name,  # a label so accountant can understand where this line come from
            'amount_currency': 0,
            'debit': abono,  # amount of debit
            'credit': 0,  # amount of credit
            'account_id': 1,  # account
            'date': datetime.datetime.now().today(),
            'partner_id': persona_id,  # partner if there is one
            'currency_id': moneda_id,
            'payment_id': pago.id,
            'invoice_id': factura_id,
            'move_id':id,
            'company_id': 1
        }

        m2={
                            'name': pago.move_name,
                            'amount_currency': 0,
                            'debit': 0,
                            'credit': abono,
                            'account_id': 3,
                            'analytic_account_id': False,
                            'date': datetime.datetime.now().today(),
                            'partner_id': persona_id,
                            'currency_id': moneda_id,
                            'payment_id': pago.id,
                            'invoice_id': factura_id,
                            'move_id':id,
                            'company_id': 1
                        }

        """
        #r1=self.env['account.move.line'].with_context(check_move_validity=False).create(m2)
        #r2=self.env['account.move.line'].with_context(check_move_validity=False).create(m1)

        #print("***Movimeinto: m1" + str(m1) + " m2" + str(m2))
        #move_line_ids line_ids
        #pago.update({'move_line_ids': [(0, 0, m1),(0, 0, m2)]})
        #pago.update({'move_line_ids': [(0, 0, m2)]})

        #asiento = self.env['account.move'].create(registro)
        #asiento.post()

    def truncar2(self,valor):
        return math.trunc(valor*100.00)/100.00

    def truncar3(self,valor):
        return math.trunc(valor*1000.00)/100.00
    
    def truncar4(self,valor):
        return math.trunc(valor*10000.00)/10000.00
    
    def _generar_nota_cargo(self, vals, tipo, parametros_obj):
        configuracion_trafitec = vals.env['trafitec.parametros'].search([('company_id', '=',vals.company_id.id)]) #Plan contable.

        diario = vals.env['account.journal'].search([('id', '=', configuracion_trafitec.cr_diario_id.id)]) #Diario.
        nca_diario_pagos_id = vals.env['account.journal'].search([('id', '=', configuracion_trafitec.nca_diario_pagos_id.id)]) #Diario para pagos de nota de cargo.
        nca_diario_cobros_id = vals.env['account.journal'].search([('id', '=', configuracion_trafitec.nca_diario_cobros_id.id)]) #Diario para cobros de notas de cargo.
        plancontable = vals.env['account.account'].search([('id', '=', configuracion_trafitec.cr_plancontable_id.id)]) #Plan contable.

        error = False
        errores = ''

        #print("***********ENTRO NOTA CAGO 2***************")
        if not vals.asociado_id.customer:
            error = True
            errores +='\nEl asociado tambien debe ser cliente.'

        if not diario:
            error = True
            errores += '\nNo se ha especificado un diario en contabilidad con el nombre: Proveedores Transportistas.'

        if not plancontable:
            error = True
            errores += '\nNo se ha especificado un plan contable en contabilidad con el nombre: Proveedores Transportistas.'

        if not configuracion_trafitec:
            error = True
            errores += '\nNo se ha especificado los parametros de trafitec: Trafitec/Sistema/Parametros.'

        if not vals.asociado_id.uso_cfdi_id:
            error = True
            errores += '\nDebe especificar el uso del cfdi del Cliente.'

        if not vals.asociado_id.pay_method_id:
            error = True
            errores += '\nDebe especificar el método de pago del Cliente.'

        if not parametros_obj.iva.account_id:
            error = True
            errores += '\nLos impuestos de IVA no tienen cuenta de impuestos.'

        if not parametros_obj.retencion.account_id:
            error = True
            errores += '\nLos impuestos de IVA retenido no tiene cuenta de impuestos.'

        if error:
            raise UserError(_('Alerta..\n'+errores))

        if tipo == 'merma':
            monto = self.mermas_des
        elif tipo == 'descuento':
            monto = self.descuento_des
        elif tipo == 'comision':
            monto = self.comision_des
        elif tipo == 'pronto':
            monto = self.prontopago_des
        elif tipo == 'diferencia':
            monto = self.diferencia

        if monto <= 0:
            return

        piva = (parametros_obj.iva.amount / 100)
        priva = (parametros_obj.retencion.amount / 100)

        c_subtotal = self.truncar4(monto/(1+(piva+priva)))
        c_iva = c_subtotal * piva
        c_riva = c_subtotal * priva
        c_total = c_subtotal + c_iva + c_riva


        subtotal = c_subtotal
        iva = c_iva
        riva = c_riva
        total = c_total
        
        print("**TOTALES: subtotal:"+str(subtotal)+" iva:"+str(iva)+" riva:"+str(riva)+" total:"+str(total))
        
        #Hacer ajuste.
        if total <= 0:
            raise UserError(_('Alerta..\nEl total de la nota es menor o igual a cero.'))
            return

        #print("***********************************************vals**************************************************")
        #print(vals)
        #Documento general.
        valores = {
            'origin': vals.name,
            #'type': 'in_refund',
            'type': 'out_invoice',
            'date_invoice': datetime.datetime.now(),
            'partner_id': vals.asociado_id.id,
            'journal_id': diario.id,
            'company_id': vals.company_id.id,
            'currency_id': vals.currency_id.id,

            #Datos de cfdi..
            'uso_cfdi_id': vals.asociado_id.uso_cfdi_id.id, #Mike.
            'pay_method_id': vals.asociado_id.pay_method_id.id, #Mike.  pay.method
            'metodo_pago_id': configuracion_trafitec.metodo_pago_id.id, #Mike.  sat.metodo.pago

            'account_id': plancontable.id,
            'reference': 'Nota de cargo por {} generada del contra recibo {} / {} '.format(tipo, vals.name, self.invoice_id.reference)
        }
        invoice_id = vals.env['account.invoice'].create(valores)
        #invoice_id.update({'tax_line_ids': [(6, 0, [parametros_obj.iva.id, parametros_obj.retencion.id])]})

        #Registra los metodos de pago.
        invoice_id.update({'pay_method_ids': [(6, 0, [vals.asociado_id.pay_method_id.id])]})
        #invoice_id.update({'invoice_tax_ids': [(6, 0, [parametros_obj.iva.id, parametros_obj.retencion.id])]})

        #Metodos de pago relacionados.
        #account_invoice_pay_method_rel invoice_id->account_invoice pay_method_id->pay_method
        valores={
            'invoice_id': invoice_id,
            'pay_method_id': vals.asociado_id.pay_method_id.id
        }

        #print("******************************************** VALS.ENV",vals.env)
        #metodospago=vals.env['account.invoice.pay_method_rel'].create(valores)
        #if not metodospago:

        #print("**********NOTA DE CARGO",valores)

        product = self.env['product.product'].search([('product_tmpl_id', '=', parametros_obj.product.id)])

        #Conceptos del documento.
        inv_line = {
            'invoice_id': invoice_id.id,
            'product_id': product.id,
            'name': 'Nota de cargo por {} generada del contra recibo {} / {} '.format(tipo,vals.name,self.invoice_id.reference),
            
            'account_id': product.property_account_income_id.id,
            # order.lines[0].product_id.property_account_income_id.id or order.lines[0].product_id.categ_id.property_account_income_categ_id.id,
            'uom_id': parametros_obj.uom.uom_id.id,
            'quantity': 1,
            'price_unit': subtotal,
            'discount': 0
        }                                          

        #Obtener impuestos del producto.
        #Impuestos del producto para compras: product_supplier_taxes_rel  /   prod_id->product_template tax_id->account_tax
        #Impuestos del producto para ventas: product_taxes_rel / prod_id->product_template tax_id->account_tax

        #impuestos=vals.env['product.taxes.rel'].search([('prod_id','=',product.id)])
        #print("**********IMPUESTOS:",impuestos)
        #Impuestos por linea de factura: account_invoice_line_tax / tax_id->account_tax invoice_line_id->account_invoice_line

        linea_id = vals.env['account.invoice.line'].create(inv_line)
        #print("**********NOTA DE CARGO LINEA", inv_line)

        #Crea los impuestos relacionados con la linea.
        linea_id.update({'invoice_line_tax_ids': [(6, 0, [parametros_obj.iva.id, parametros_obj.retencion.id])]})
        
        #Crea los impuestos del documento.
        #documento_impuestos=[]
        inv_tax = {
            'invoice_id': invoice_id.id,
            'name': parametros_obj.iva.name,
            'account_id': parametros_obj.iva.account_id.id,
            'amount': iva,
            'tax_id': parametros_obj.iva.id,
            'sequence': '0'
        }
        #documento_impuestos.append(inv_tax)
        
        #vals.env['account.invoice.tax'].create(inv_tax) #Buena.
        
        #invoice_id.compute_taxes()
        #print("**********NOTA DE CARGO IVA", inv_tax)

        inv_ret = {
            'invoice_id': invoice_id.id,
            'name': parametros_obj.retencion.name,
            'account_id': parametros_obj.retencion.account_id.id,
            'amount': riva,
            'tax_id': parametros_obj.retencion.id,
            'sequence': '0'
        }
        #documento_impuestos.append(inv_ret)
        #vals.env['account.invoice.tax'].create(inv_ret)

        #Valida la nota.
        try:
            invoice_id.compute_taxes()  # Calcula impuestos.
        except Exception as err:
            raise UserError("Error al aplicar los impuestos de la nota de cargo: {}.".format(str(err)))
        try:
            invoice_id.action_invoice_open()  # Contabiliza la nota de cargo e intenta timbrarla.
        except Exception as err:
            raise UserError("Error al validar la nota de cargo: {}.".format(str(err)))

        if invoice_id.state != 'open':
            raise UserError("No fue posible validar la nota de cargo: {}.".format(str(invoice_id.state)))
        #raise UserError(_('Alerta..\n'+errores))
        #if diario.use_for_cfdi and not invoice_id.sat_uuid:
        #    print("Error, la nota no se timbro.")
        #    raise UserError(_('Alerta..\nNo fue posible timbrar la nota de cargo.'))
        #nca_diario_pagos_id
        #nca_diario_cobros_id

        if total > 0:
            #pass
            # Pago de factura.
            self._aplicapago(nca_diario_pagos_id.id, self.invoice_id.id, invoice_id.amount_total, vals.currency_id.id, self.asociado_id.id, 'supplier', 'outbound')

            #Pago de nota de cargo.
            self._aplicapago(nca_diario_cobros_id.id, invoice_id.id, invoice_id.amount_total, vals.currency_id.id, self.asociado_id.id, 'customer', 'inbound')

        #return {'warning': {'message': '1', 'title': '2', 'field': 'state'}}
        #print("**********NOTA DE CARGO CONTABILIZADA")

        return invoice_id

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


    
    def action_available(self):
        error = False
        errores = ""

        #Validaciones.
        if not self.invoice_id:
            error = True
            errores += "Debe especificar la carta porte.\r\n"

        if not self.viaje_id:
            error = True
            errores += "Debe especificar al menos un viaje.\r\n"


        #-------------------------------------------
        #Guardar datos calculados.
        #-------------------------------------------
        self.fletesx = 0
        self.maniobrasx = 0
        for v in self.viaje_id:
            self.fletesx += v.flete_asociado
            self.maniobrasx += v.maniobras
        
        self.total_abonox_des = self.total_abono_des
        self.total_saldox_des = self.total_saldo_des
        
        self.total_abonox_coms = self.total_abono_coms
        self.total_saldox_coms = self.total_saldo_coms
        

        self.descuentox_antes = self.descuento_antes
        self.descuentox_des = self.descuento_des
        
        self.mermasx_antes = self.mermas_antes
        self.mermasx_des = self.mermas_des
        
        self.comisionesx_antes = self.comisiones_antes
        self.comisionx_des = self.comision_des
        
        self.prontopagox_antes = self.prontopago_antes
        self.prontopagox_des = self.prontopago_des
        
        # Totales x
        self.subtotalx = self.fletesx+self.maniobrasx-self.mermasx_antes-self.descuentox_antes-self.comisionesx_antes-self.prontopagox_antes
        self.subtotalx_sm = self.fletesx-self.mermasx_antes-self.descuentox_antes-self.comisionesx_antes-self.prontopagox_antes

        self.ivax = 0
        if self.iva_option == "CIR" or self.iva_option == "CISR":
            self.ivax = self.subtotalx * 0.16

        self.rivax = 0
        if self.iva_option == "CIR":
            self.rivax = self.subtotalx_sm * 0.04
        
        self.totalx = self.subtotalx+self.ivax-self.rivax
        
        #Diferencia entre contra recibo y carta porte.
        self.diferenciax = self.invoice_id.amount_total - self.totalx
        self.notacargox = self.diferenciax

        # -------------------------------------------
        
        #if self.diferencia>0:
        #    if not self.notascargo_diario_id:
        #        error=True
        #        errores+="Debe especificar el diario para las notas de cargo.\n"


        #cartasportes=self.env['trafitec.contrarecibo'].search([('invoice_id','=',self.invoice_id.id),('id','!=',self.id)])
        #print("***Cartas porte: "+str(cartasportes))

        if self.invoice_id:
            if self.invoice_id.amount_total <= 0:
                error = True
                errores += "El total de la carta porte debe ser mayor a cero.\r\n"

        viajes_encp = False

        for viaje in self.viaje_id:
            vobj = self.env['trafitec.viajes'].search([('id', '=', viaje.id)])
            #Obtener los cargos adiionales.
            fl_obj = self.env['account.invoice.line']
            vca_obj = self.env['trafitec.viaje.cargos']
            
            fl_dat = fl_obj.search([('invoice_id', '=', self.invoice_id.id)])
            vca_dat = vca_obj.search([('line_cargo_id', '=', viaje.id), ('validar_en_cr', '=', True)])

            #TODO Habilitar cuando se pruebe bien cargos adicionales.
            """
            if len(vca_dat) > 0:
                for vca in vca_dat:
                    existe = False
                    for fl in fl_dat:
                        if fl.product_id.id == vca.name.product_id.id and vca.valor == fl.price_subtotal:
                            existe = True
                            break
                    if not existe:
                        error = True
                        errores += "No se encontro el cargo adicional '{} por {:.2f}' del viaje '{}' en la factura '{}'.\r\n".format(vca.name.name, vca.valor, viaje.name, ((self.invoice_id.number or self.invoice_id.name or "")+" / "+(self.invoice_id.reference or "")))
            """
            
            #Validar que los viajes tambien esten en la carta porte.
            viaje_encp = False
            for vcp in self.invoice_id.viajescp_id:
                if vcp.id == viaje.id:
                    viaje_encp = True
                    break

            if not viaje_encp:
                error = True
                errores += 'El viaje {} no se encontro en los viajes de la carta porte.\r\n'.format(viaje.name)
            #----------------------------------------------------------

            if vobj.en_contrarecibo:
                error = True
                errores += 'El viaje {} ya tiene contra recibo.\r\n'.format(viaje.name)

            if viaje.documentacion_completa == False:
                error = True
                errores += 'El viaje con el folio: {} no tiene documentación completa.\r\n'.format(viaje.name)

            if viaje.peso_origen_total == 0:
                error = True
                errores += 'El viaje con el folio: {} no tiene el peso origen capturado.\r\n'.format(viaje.name)

            if viaje.peso_destino_total == 0:
                error = True
                errores += 'El viaje con el folio: {} no tiene el peso destino capturado.\r\n'.format(viaje.name)

            if viaje.peso_convenido_total == 0:
                error = True
                errores += 'El viaje con el folio: {} no tiene el peso convenido capturado.\r\n'.format(viaje.name)

            #Revisar boletas.
            boletas = self.env['trafitec.viajes.boletas'].search([('linea_id', '=', viaje.id)])
            if not boletas:
                error = True
                errores += 'El viaje con el folio {} no tiene boletas.\r\n'.format(viaje.name)
            
            #relacion=self.env['trafitec.viajesxcontrarecibo']
            #relacion.create({'viaje_id':viaje.id,'contrarecibo_id':self.id,'factura_id':self.invoice_id.id})

        #Totales.
        totales = self.totales()
        #print("------------------Totales:"+str(totales))
        if totales['subtotal'] <= 0:
            error = True
            errores += "El subtotal debe ser mayor a cero.\n"

        if totales['total'] <= 0:
            error = True
            errores += "El total debe ser mayor a cero.\n"


        if self.invoice_id:
            diferencia=abs(totales['total']-self.invoice_id.amount_total)
            if totales['total'] > self.invoice_id.amount_total and diferencia > 1:
                error=True
                errores+="El total de la carta porte debe ser mayor o igual al total del contra recibo.\n"

        if error:
            raise UserError(_(errores))


        #Proceso.
        parametros_obj = self._get_parameter_company(self)
        if self.subtotal_g > 0:
            #invoice_id = self._crear_factura_proveedor(self)
            self._cobrar_descuentos()
            self._cobrar_comisiones()
            
            """
            if self.mermas_bol == True and self.mermas_des > 0:
                invoice = self._generar_nota_cargo(self,'merma',parametros_obj)
                self.folio_merma = invoice
            
            if self.descuento_bol == True and self.descuento_des > 0:
                invoice = self._generar_nota_cargo(self, 'descuento',parametros_obj)
                self.folio_descuento = invoice
            
            if self.comision_bol == True and self.comision_des > 0:
                invoice = self._generar_nota_cargo(self, 'comision',parametros_obj)
                self.folio_comision = invoice
            
            if self.prontopago_bol == True and self.prontopago_des > 0:
                invoice = self._generar_nota_cargo(self, 'pronto',parametros_obj)
                self.folio_prontopago = invoice
            """
            
            if self.diferencia > 1: #Tolerancia de 1 peso.
                invoice = self._generar_nota_cargo(self, 'diferencia', parametros_obj)
                self.folio_diferencia = invoice

            #Marca los viajes como que ya tienen contra recibo.
            for viaje in self.viaje_id:
                viaje.with_context(validar_credito_cliente=False).write({'en_contrarecibo': True, 'factura_proveedor_id': self.invoice_id.id, 'contrarecibo_id': self.id})

            #Actualiza los estados de la factura.
            #print("******SELF ID: "+str(self.id))
            try:
                self.invoice_id.write({'factura_encontrarecibo': True, 'es_cartaporte': True, 'contrarecibo_id': self.id})
            except TypeError:
                raise UserError(_('Alerta..\nError al marcar la factura {} como: En contra recibo.'.format(self.invoice_id.name)))

            #Establece el estado a Validada.
            self.write({'state': 'Validada'})

    #Cancelar contra recibo.
    
    def action_cancel(self):
        if self.state == 'Validada':
            #Validacion.
            if self.invoice_id.state == 'open' or self.invoice_id.state == 'paid':
                raise UserError(_('Alerta !\nLa factura carta porte ya fue contabilizada, no podra cancelar el contra recibo.'))

            if self.folio_diferencia:
                if self.folio_diferencia.state == 'open' or self.folio_diferencia.state == 'paid':
                    raise UserError(_('Alerta !\nLa nota de cargo por diferencia ya fue contabilizada, no podra cancelar el contra recibo.'))

            if self.folio_merma:
                if self.folio_merma.state == 'open':
                    raise UserError(_('Alerta !\nLa nota de cargo por merma ya fue contabilizada, no podra cancelar el contra recibo.'))

            if self.folio_descuento:
                if self.folio_descuento.state == 'open':
                    raise UserError(_('Alerta !\nLa nota de cargo por descuentos ya fue contabilizada, no podra cancelar el contra recibo.'))

            if self.folio_comision:
                if self.folio_comision.state == 'open':
                    raise UserError(_('Alerta !\nLa nota de cargo por comision ya fue contabilizada, no podra cancelar el contra recibo.'))

            if self.folio_prontopago:
                if self.folio_prontopago.state == 'open':
                    raise UserError(_('Alerta !\nLa nota de cargo por pronto pago ya fue contabilizada, no podra cancelar el contra recibo.'))

            #Libera comisiones relacionadas.
            for comision in self.comision_id:
                comision_obj = self.env['trafitec.comisiones.abono'].search([('abonos_id','=',comision.cargo_id.id),('permitir_borrar','=',True)])
                for c in comision_obj:
                    c.write({'permitir_borrar': False})
                    c.unlink()

            #Libera descuentos relacionados.
            for descuento in self.descuento_id:
                descuento_obj = self.env['trafitec.descuentos.abono'].search([('abonos_id','=',descuento.descuento_fk.id),('permitir_borrar','=',True)])
                for d in descuento_obj:
                    d.write({'permitir_borrar':False})
                    d.unlink()

            #Liberar factura de proveedor.
            self.invoice_id.write({'factura_encontrarecibo':False,'contrarecibo_id':False})

            #Marca los viajes como que ya no tienen contra recibo.
            for viaje in self.viaje_id:
                #vobj=self.env['trafitec.viajes'].search([('id','=',viaje.id)])
                #if vobj.en_contrarecibo: #and vobj.factura_proveedor_id.id==self.invoice_id.id:
                viaje.with_context(validar_credito_cliente=False).write({'en_contrarecibo': False, 'factura_proveedor_id': False, 'contrarecibo_id': False})


        #Quitar viajes relacionados.
        self.viaje_id = [(5, _, _)]
        self.fletes = 0

        #Quitar cargos adicionales.
        self.cargosadicionales_id = [(5, _, _)]
        self.cargosadicionales_total = 0
        #TODO
        #Quitar comisiones.

        #Quitar carta porte.
        self.invoice_id = False

        #Quitar nota de cargo.
        self.folio_diferencia = False

        #Establece el estado a cancelada.
        self.write({'state': 'Cancelada'})

    def _carga_viajes(self):
        return
        if self.state == 'Nueva' and self.asociado_id and self.currency_id and self.lineanegocio and self.iva_option:
            self.viaje_id = []
            viajes=self.env['trafitec.viajes'].search([('asociado_id','=',self.asociado_id.id),('en_contrarecibo','=',False),('tipo_viaje','=','Normal'),('state','=','Nueva')])
            self.viaje_id=viajes


    
    @api.onchange('asociado_id')        
    def _asociado(self):
        self.descuento_id=[]
        self.comision_id=[]

        if self.asociado_id:
            #Carga los decuentos con saldo.
            obj = self.env['trafitec.descuentos'].search([('asociado_id', '=', self.asociado_id.id), ('saldo', '>', 0), ('state', '=', 'activo')])

            rd = []
            rc = []
            for descuento in obj:
                    folio = descuento.viaje_id.name
                    operador = descuento.operador_id.name
                    abono=descuento.saldo
                    if descuento.cobro_fijo == True:
                        if descuento.monto_cobro:
                            abono = descuento.monto_cobro
                        else:
                            abono = descuento.saldo

                    valores = {
                        'name' : descuento.concepto.name ,
                        'fecha' : descuento.fecha ,
                        'anticipo' : descuento.monto ,
                        'abonos' : descuento.abono_total ,
                        'saldo' : descuento.saldo,
                        'abono' : abono,
                        'folio_viaje' : folio ,
                        'operador' : operador ,
                        'comentarios' : descuento.comentarios,
                        'descuento_fk' : descuento.id,
                        'viaje_id' : descuento.viaje_id
                    }
                    rd.append(valores)
            self.descuento_id = rd
            #print("******Descuentos: "+str(rd))

            #Carga las comisiones con saldo.
            obj_comi = self.env['trafitec.cargos'].search([('asociado_id', '=', self.asociado_id.id), ('tipo_cargo', '=', 'comision'), ('saldo', '>', 0)])

            rc = []
            for comision in obj_comi:
                    valores = {
                        'name' : comision.viaje_id.name,
                        'fecha' : comision.viaje_id.fecha_viaje,
                        'comision' : comision.monto,
                        'abonos' : comision.abonado,
                        'saldo' : comision.saldo,
                        'asociado_id' : comision.asociado_id,
                        'tipo_viaje' : comision.viaje_id.tipo_viaje,
                        'cargo_id' : comision.id,
                        'viaje_id' : comision.viaje_id
                    }
                    rc.append(valores)
            self.comision_id = rc
            #print("******Comisiones: " + str(rc))


    @api.onchange('viaje_id', 'asociado_id', 'lineanegocio')
    def _onchange_maniobras(self):
        """amount = 0
        for record in self.viaje_id:
            amount += record.maniobras
        
        self.maniobras = amount
        """
        if self.viaje_id and self.invoice_id and len(self.viaje_id) > 0:
            try:
                viaje1 = self.viaje_id[0]
                print("---VIAJE CR1---")
                print(viaje1)
                if viaje1.subpedido_id.linea_id.cotizacion_id.asociado_plazo_pago_id:
                    pterm = viaje1.subpedido_id.linea_id.cotizacion_id.asociado_plazo_pago_id
                    pterm_list = pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=self.fecha)[0]
                    fecha_vencimiento = max(line[0] for line in pterm_list)
                    
                    #Actualiza la carta porte.
                    self.invoice_id.sudo().write(
                        {
                            'payment_term_id': viaje1.subpedido_id.linea_id.cotizacion_id.asociado_plazo_pago_id.id,
                            'date_due': fecha_vencimiento
                        }
                    )
            except:
                print("TRAFITEC: Error al calcula la fecha de vencimiento de la factura de proveedor.")

    
    @api.depends('viaje_id', 'asociado_id', 'lineanegocio')
    def _compute_maniobras(self):
        maniobras = 0
        for v in self.viaje_id:
            maniobras += v.maniobras
        self.maniobras = maniobras


    
    @api.depends(
        'total',
        'total_g'
    )
    def _compute_diferencia(self):
        self.diferencia = 0
        if self.total and self.total_g:
            self.diferencia = self.total - self.total_g
            #self.notacargo = self.total - self.total_g
        #print("*********************Diferencia:"+str(self.diferencia))

    @api.onchange('mermas_des', 'descuento_des', 'comision_des', 'prontopago_des')
    def _onchange_notacargo(self):
        self.notacargo = self.mermas_des + self.descuento_des + self.comision_des + self.prontopago_des

    
    @api.depends(
        'diferencia'
    )
    def _compute_notacargo(self):
        #self.notacargo = self.mermas_des + self.descuento_des + self.comision_des + self.prontopago_des
        self.notacargo = self.diferencia

    
    @api.depends('descuento_id', 'descuento_bol')
    def _check_descuentos(self):
        if self.cobrar_descuentos:
            amount = 0
            saldo = 0
            abonos = 0
            if self.cobrar_descuentos == 'No cobrar':
                self.descuento_antes = amount
                self.total_abono_des = abonos
                self.total_saldo_des = saldo
            if self.cobrar_descuentos == 'Todos':
                for descuento in self.descuento_id:
                    amount += descuento.abono
                    abonos += descuento.abonos
                    saldo += descuento.saldo
                self.descuento_antes = amount
                self.total_abono_des = abonos
                self.total_saldo_des = saldo
            if self.cobrar_descuentos == 'Viajes del contrarecibo':
                for descuento in self.descuento_id:
                    if descuento.viaje_id in self.viaje_id:
                        amount += descuento.abono
                        abonos += descuento.abonos
                        saldo += descuento.saldo
                    self.total_abono_des = abonos
                    self.total_saldo_des = saldo
                if self.descuento_bol == False:
                    self.descuento_antes = amount
                    self.descuento_des = 0
                else:
                    self.descuento_antes = 0
                    self.descuento_des = amount
        else:
            self.descuento_antes = 0
            self.descuento_des = 0

    @api.onchange('cobrar_descuentos','descuento_id', 'viaje_id','descuento_bol')
    def _onchange_descuentos(self):
        if self.cobrar_descuentos:
            amount = 0
            saldo = 0
            abonos = 0
            if self.cobrar_descuentos == 'No cobrar':
                self.descuento_antes = amount
                self.total_abono_des = abonos
                self.total_saldo_des = saldo
            if self.cobrar_descuentos == 'Todos':
                for descuento in self.descuento_id:
                    amount += descuento.abono
                    abonos += descuento.abonos
                    saldo += descuento.saldo
                self.descuento_antes = amount
                self.total_abono_des = abonos
                self.total_saldo_des = saldo
            if self.cobrar_descuentos == 'Viajes del contrarecibo':
                for descuento in self.descuento_id:
                    if descuento.viaje_id in self.viaje_id:
                        amount += descuento.abono
                        abonos += descuento.abonos
                        saldo += descuento.saldo
                    self.total_abono_des = abonos
                    self.total_saldo_des = saldo
                if self.descuento_bol == False:
                    self.descuento_antes = amount
                    self.descuento_des = 0
                else:
                    self.descuento_antes = 0
                    self.descuento_des = amount
        else:
            self.descuento_antes = 0
            self.descuento_des = 0

    def TotalMermas(self):
        total = 0
        for v in self.viaje_id:
            total += v.merma_cobrar_pesos

        return total

    #Mermas
    @api.onchange('viaje_id', 'mermas_bol')
    def _onchange_mermas(self):
        total = 0
        self.mermas_antes=0
        for v in self.viaje_id:
            total += v.merma_cobrar_pesos
        self.mermas_antes=total

    #Mermas
    @api.onchange('viaje_id', 'asociado_id')
    def _onchange_viaje_id(self):
        self.cargosadicionales_id = [(5, _, _)]
        conceptos = []
        total = 0
        # Cargo para cartas porte.
        for v in self.viaje_id:
            # Cargos adicionales
            cargos = self.env['trafitec.viaje.cargos'].search([
                ('line_cargo_id', '=', v.id),
                ('tipo', 'in', ('pagar_cr_cobrar_f', 'pagar_cr_nocobrar_f')),
                ('valor', '>', 0)
            ])
            for c in cargos:
                #Concepto.
                cargo = {
                    'viaje_id': c.line_cargo_id.id,
                    'contrarecibo_id': self._origin.id,
                    'tipo_cargo_id': c.name.id,
                    'valor': c.valor
                }
                conceptos.append(cargo)
                total += c.valor

        _logger.info("-------------------------CARGOS ADICIONAES--------------------")
        _logger.info(str(conceptos))
        self.cargosadicionales_id = conceptos

    
    @api.depends('cargosadicionales_id')
    def _compute_otros(self):
        total = 0
        self.cargosadicionales_total = 0
        for c in self.cargosadicionales_id:
            total += c.valor

        self.cargosadicionales_total = total



    
    @api.depends('viaje_id', 'mermas_bol')
    def _compute_mermas_antes(self):
        total = 0
        self.mermas_antes = 0

        #print("MERMAS ANTES BOOL: "+str(self.mermas_bol))

        for v in self.viaje_id:
            total += v.merma_cobrar_pesos

        if self.mermas_bol == False:
            self.mermas_antes = total
        #print("=================Compute mermas antes:"+str(self.mermas_antes)+" Mermas bol:"+str(self.mermas_bol))

    @api.onchange('viaje_id','mermas_bol')
    def _onchange_mermas_antes(self):
        total = 0
        self.mermas_antes = 0
        #print("MERMAS ANTES BOOL: " + str(self.mermas_bol))

        for v in self.viaje_id:
            total += v.merma_cobrar_pesos

        if self.mermas_bol == False:
            self.mermas_antes = total

    
    @api.depends('viaje_id','mermas_bol')
    def _compute_mermas_despues(self):
        total = 0
        self.mermas_des = 0

        for v in self.viaje_id:
            total += v.merma_cobrar_pesos

        if self.mermas_bol == True:
            self.mermas_des = total


    #Pronto pago.
    
    @api.depends('viaje_id', 'prontopago_bol')
    def _compute_prontopago(self):
        if self.viaje_id:
            amount = 0
            parametros_obj = self._get_parameter_company(self)
            for viaje in self.viaje_id:
                if viaje.pronto_pago == True:
                    amount += viaje.flete_asociado * (parametros_obj.pronto_pago / 100)
            if self.prontopago_bol == True:
                self.prontopago_des = amount
                self.prontopago_antes = 0
            else:
                self.prontopago_antes = amount
                self.prontopago_des = 0

    @api.onchange('viaje_id','prontopago_bol')
    def _onchange_prontopago(self):
        if self.viaje_id:
            amount = 0
            parametros_obj = self._get_parameter_company(self)
            for viaje in self.viaje_id:
                if viaje.pronto_pago == True:
                    amount += viaje.flete_asociado * (parametros_obj.pronto_pago / 100)
            if self.prontopago_bol == True:
                self.prontopago_des = amount
                self.prontopago_antes = 0
            else:
                self.prontopago_antes = amount
                self.prontopago_des = 0


    
    @api.depends('viaje_id', 'comision_bol', 'cobrar_comisiones')
    def _check_comisiones(self):
        if self.cobrar_comisiones:
            amount = 0
            saldo = 0
            abonos = 0
            if self.cobrar_comisiones == 'No cobrar':
                self.comisiones_antes = amount
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.cobrar_comisiones == 'Todos los viajes':
                for comisi in self.comision_id:
                    amount += comisi.saldo
                    saldo += comisi.saldo
                    abonos += comisi.abonos
                self.comisiones_antes = amount
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.cobrar_comisiones == 'Viajes del contrarecibo':
                for comisi in self.comision_id:
                    if comisi.viaje_id in self.viaje_id:
                        amount += comisi.saldo
                        saldo += comisi.saldo
                        abonos += comisi.abonos
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.comision_bol == False:
                self.comisiones_antes = amount
                self.comision_des = 0
            else:
                self.comisiones_antes = 0
                self.comision_des = amount
        else:
            self.comisiones_antes = 0
            self.comision_des = 0

    @api.onchange('cobrar_comisiones', 'comision_id', 'viaje_id', 'comision_bol')
    def _onchange_comisiones(self):
        if self.cobrar_comisiones:
            amount = 0
            saldo = 0
            abonos = 0
            if self.cobrar_comisiones == 'No cobrar':
                self.comisiones_antes = amount
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.cobrar_comisiones == 'Todos los viajes':
                for comisi in self.comision_id:
                    amount += comisi.saldo
                    saldo += comisi.saldo
                    abonos += comisi.abonos
                self.comisiones_antes = amount
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.cobrar_comisiones == 'Viajes del contrarecibo':
                for comisi in self.comision_id:
                    if comisi.viaje_id in self.viaje_id:
                        amount += comisi.saldo
                        saldo += comisi.saldo
                        abonos += comisi.abonos
                self.total_saldo_coms = saldo
                self.total_abono_coms = abonos
            if self.comision_bol == False:
                self.comisiones_antes = amount
                self.comision_des = 0
            else:
                self.comisiones_antes = 0
                self.comision_des = amount
        else:
            self.comisiones_antes = 0
            self.comision_des = 0

    
    @api.depends('viaje_id', 'viaje_id.flete_asociado')
    def _compute_fletes(self):
            # for rec in self:
            #print(">>>>>>VIAJES:::: " + str(self.viaje_id))

            self.fletes = 0
            for v in self.viaje_id:
                self.fletes += v.flete_asociado

    
    @api.depends(
        'fletes',
        'maniobras',
        'mermas_antes',
        'descuento_antes',
        'comisiones_antes',
        'prontopago_antes',
        'cargosadicionales_total'
    )
    def _compute_subtotal(self):
            # Subtotal con maniobras.
            x_mermas_antes = 0
            if self.mermas_bol == False:
                x_mermas_antes = self.TotalMermas()

            #print("***COMPUTE SUBTOTAL mermas_antes: " + str(self.mermas_antes))
            self.subtotal_g = self.fletes + self.maniobras+self.cargosadicionales_total - x_mermas_antes - self.descuento_antes - self.comisiones_antes - self.prontopago_antes

    
    @api.depends(
        'fletes',
        'mermas_antes',
        'descuento_antes',
        'comisiones_antes',
        'prontopago_antes',
        'cargosadicionales_total'
    )
    def _compute_subtotalSM(self):
            # Subtotal sin maniobras.
            self.subtotal_gSM = self.fletes+self.cargosadicionales_total - self.mermas_antes - self.descuento_antes - self.comisiones_antes - self.prontopago_antes



    
    @api.depends('subtotal_g', 'iva_option','fletes')
    def _compute_iva_g(self):
            # for rec in self:
            self.iva_g = 0
            if self.iva_option == "CIR" or self.iva_option == "CISR":
                self.iva_g = self.subtotal_g * 0.16

    
    @api.depends('subtotal_gSM', 'iva_option','fletes')
    def _compute_r_iva_g(self):
            # for rec in self:
            self.r_iva_g = 0
            if self.iva_option == "CIR":
                self.r_iva_g = self.subtotal_gSM * 0.04

    
    @api.depends('subtotal_g', 'iva_g', 'r_iva_g')
    def _compute_total_g(self):
            # for rec in self:
            self.total_g = self.subtotal_g + self.iva_g - self.r_iva_g

    #----------------------------------------------------------------------------------------------------------------------------------------------
    # TOTALES
    #----------------------------------------------------------------------------------------------------------------------------------------------
    fletes = fields.Float(string='+Fletes', compute='_compute_fletes', store=True)
    fletes_ver = fields.Float(string='+Fletes', related='fletes', readonly=True)
    fletesx = fields.Float(string='+Fletes_')
    maniobras = fields.Float(string='+Maniobras', compute='_compute_maniobras')
    maniobras_ver = fields.Float(string='+Maniobras', related='maniobras', readonly=True)
    cargosadicionales_total = fields.Float(
        string='+Cargos adicionales',
        default=0,
        store=True,
        compute=_compute_otros,
        help='Total de cargos adicionales.'
    )
    cargosadicionales_total_ver = fields.Float(string='+Cargos adicionales', related='cargosadicionales_total', default=0, help='Total de cargos adicionales.')
    maniobrasx = fields.Float(string='+Maniobras_')

    total_abono_des = fields.Float(string='Total de abono descuento', compute='_check_descuentos')
    total_abonox_des = fields.Float(string='Total de abono descuento_')
    total_saldo_des = fields.Float(string='Total de saldo descuento', compute='_check_descuentos')
    total_saldox_des = fields.Float(string='Total de saldo descuento_')

    total_abono_coms = fields.Float(string='Total de abono comision', compute='_check_comisiones')
    total_abonox_coms = fields.Float(string='Total de abono comision_')
    total_saldo_coms = fields.Float(string='Total de saldo comision', compute='_check_comisiones')
    total_saldox_coms = fields.Float(string='Total de saldo comision_')

    diferencia = fields.Float(string='Diferencia', compute='_compute_diferencia')
    diferencia_ver = fields.Float(string='Diferencia', related='diferencia')
    diferenciax = fields.Float(string='Diferencia_')
    notacargo = fields.Float(string='Nota de cargo', compute='_compute_notacargo')
    notacargo_ver = fields.Float(string='Nota de cargo', related='notacargo')
    notacargox = fields.Float(string='Nota de cargo_')


    name = fields.Char(string='Folio', default='Nuevo')
    asociado_id = fields.Many2one('res.partner', string="Asociado",domain="[('asociado','=',True),('supplier','=',True)]", required=True,track_visibility='onchange')
    currency_id = fields.Many2one("res.currency", string="Moneda", required=True,default=lambda self: self._predeterminados_moneda(),track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env['res.company']._company_default_get('trafitec.contrarecibo'))
    viaje_id = fields.Many2many('trafitec.viajes','contrarecibo_viaje_relation', 'contrarecibo_id','viajes_id', string='Viajes',domain="[('asociado_id','=',asociado_id),('moneda','=',currency_id),('lineanegocio','=',lineanegocio),('state','=','Nueva'),('en_contrarecibo','=',False),('tipo_viaje','=','Normal')]")
    # viajex_id = fields.Many2many(string='Viajes X',comodel_name='trafitec.viajes')
    cobrar_descuentos = fields.Selection([('No cobrar', 'No cobrar'), ('Todos', 'Todos'),('Viajes del contrarecibo', 'Viajes del contrarecibo')],string='Cobrar descuentos', default='Todos', required=True,track_visibility='onchange')
    cobrar_comisiones = fields.Selection([('No cobrar', 'No cobrar'), ('Viajes del contrarecibo', 'Viajes del contrarecibo'),('Todos los viajes', 'Todos los viajes')], string='Cobrar comisiones', default='Todos los viajes',required=True, track_visibility='onchange')
    iva_option = fields.Selection([('CIR', 'Con IVA y con RIVA'), ('SIR', 'Sin IVA y sin RIVA'), ('CISR', 'Con IVA y sin RIVA')],string='IVA', default='CIR', required=True, track_visibility='onchange')
    state = fields.Selection([('Nueva', 'Nueva'), ('Validada', 'Validada'), ('Cancelada', 'Cancelada')],string='Estado', default='Nueva', track_visibility='onchange')
    lineanegocio = fields.Many2one('trafitec.lineanegocio', string='Linea de negocios', required=True,default=lambda self: self._predeterminados_lineanegocio(),track_visibility='onchange')
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Factura proveedor',
        domain="[('type','=','in_invoice'),('partner_id','=',asociado_id),('amount_total','>',0),('factura_encontrarecibo','=',False),('state','=','open'),('es_cartaporte','=',True)]",
        track_visibility='onchange'
    )
    fecha = fields.Date(string='Fecha', readonly=True, index=True, copy=False, default=fields.Datetime.now,track_visibility='onchange')
    normal = fields.Boolean(string='Normal', default=True, track_visibility='onchange')
    psf = fields.Boolean(string='PSF', default=False, track_visibility='onchange')
    factura_actual = fields.Many2one('account.invoice', string='Factura proveedor actual',domain="[('type','=','in_invoice'),('partner_id','=',asociado_id),('amount_total','>',0)]")
    cargospendientes_id = fields.One2many(comodel_name='trafitec.cargospendientes', inverse_name='contrarecibo_id', string='Cargos pendientes')
    x_folio_trafitecw = fields.Char(string='Folio Trafitec Windows', help="Folio del contra recibo en Trafitec para windows.",track_visibility='onchange')

    #----------------------------------------------------------------------------------------------------------------------------------------------
    # MONTOS
    #----------------------------------------------------------------------------------------------------------------------------------------------
    #despues
    mermas_bol = fields.Boolean(string='Merma', default=False, track_visibility='onchange')
    mermas_des = fields.Float(string='-Merma', store=False, compute='_compute_mermas_despues')
    mermas_des_ver = fields.Float(string='-Merma', related='mermas_des')
    mermasx_des = fields.Float(string='-Merma', store=True)

    mermas_antes = fields.Float(string='-Merma', store=False, compute='_compute_mermas_antes')
    mermas_antes_ver = fields.Float(string='-Merma', related='mermas_antes')
    mermasx_antes = fields.Float(string='-Merma', store=True)

    descuento_bol = fields.Boolean(string='Descuento', default=False, track_visibility='onchange')
    descuento_des = fields.Float(string='-Descuento', store=False, compute='_check_descuentos')
    descuento_des_ver = fields.Float(string='-Descuento', related='descuento_des')
    descuentox_des = fields.Float(string='-Descuento_', store=True)

    descuento_antes = fields.Float(string='-Descuento', store=False, compute='_check_descuentos')
    descuento_antes_ver = fields.Float(string='-Descuento', related='descuento_antes')
    descuentox_antes = fields.Float(string='-Descuento_', store=True)

    comision_bol = fields.Boolean(string='Comision', default=False, track_visibility='onchange')
    comision_des = fields.Float(string='-Comision', store=False, compute='_check_comisiones')
    comision_des_ver = fields.Float(string='-Comision', related='comision_des')
    comisionx_des = fields.Float(string='-Comision_', store=True)

    comisiones_antes = fields.Float(string='-Comisiones', store=False, compute='_check_comisiones')
    comisiones_antes_ver = fields.Float(string='-Comisiones', related='comisiones_antes')
    comisionesx_antes = fields.Float(string='-Comisiones_', store=True)

    prontopago_bol = fields.Boolean(string='Pronto pago', default=False, track_visibility='onchange')
    prontopago_des = fields.Float(string='-Pronto pago', store=False, compute='_compute_prontopago')
    prontopago_des_ver = fields.Float(string='-Pronto pago', related='prontopago_des')
    prontopagox_des = fields.Float(string='-Pronto pago_', store=True)

    prontopago_antes = fields.Float(string='-Pronto pago', store=False, compute='_compute_prontopago')
    prontopago_antes_ver = fields.Float(string='-Pronto pago', related='prontopago_antes')
    prontopagox_antes = fields.Float(string='-Pronto pago_', store=True)


    #CR Totales
    subtotal_g = fields.Float(string='Subtotal', store=True, compute='_compute_subtotal')
    subtotal_gSM = fields.Float(string='Subtotal SM (Sin maniobras)', store=True, compute='_compute_subtotalSM')
    iva_g = fields.Float(string='IVA', store=True, readonly=True, compute='_compute_iva_g')
    r_iva_g = fields.Float(string='RIVA', store=True, compute='_compute_r_iva_g')
    total_g = fields.Float(string='Total', store=True, compute='_compute_total_g')

    subtotal_g_ver = fields.Float(string='Subtotal', related="subtotal_g", readonly=True)
    iva_g_ver = fields.Float(string='IVA', related="iva_g", readonly=True)
    r_iva_g_ver = fields.Float(string='RIVA', related="r_iva_g", readonly=True)
    total_g_ver = fields.Float(string='Total', related="total_g", readonly=True)

    subtotalx = fields.Float(string='Subtotal_', store=True)
    subtotalx_sm = fields.Float(string='Subtotal sm_', store=True)
    ivax = fields.Float(string='IVA_', store=True)
    rivax = fields.Float(string='RIVA_', store=True)
    totalx = fields.Float(string='Total_', store=True)

    #Carta-porte
    folio = fields.Char(string='Folio carta porte', related='invoice_id.reference', store=True)
    fecha_porte = fields.Date(string='Fecha', related='invoice_id.date_invoice', store=True)
    fletes_carta_porte = fields.Float(string='Fletes')

    subtotal = fields.Monetary(string='Subtotal', related='invoice_id.amount_untaxed')

    observaciones = fields.Text(string="Observaciones",_constraints = [_validaobservacione, "Observaciones invalidas", ['observaciones','state']],track_visibility='onchange')

    r_iva = fields.Float(string='R. IVA', compute='_compute_r_iva_carta')

    total = fields.Monetary(string='Total', related='invoice_id.amount_total')

    carta_porte = fields.Boolean(string='Carta porte')
    cfd = fields.Boolean(string='CFD')
    iva = fields.Float(string='IVA', compute='_compute_iva_carta')

    #Relaciones de descientos y comisiones relacionadas con el contra recibo
    descuento_id = fields.One2many(comodel_name="trafitec.con.descuentos", inverse_name="linea_id")
    comision_id = fields.One2many(comodel_name="trafitec.con.comision", inverse_name="line_id")
    cargosadicionales_id = fields.One2many(string="Cargos adicionales", comodel_name="trafitec.contrarecibos.cargos", inverse_name="contrarecibo_id")

    #Notas de cargo
    folio_diferencia = fields.Many2one('account.invoice', readonly=True, string='Folio por diferencia')
    folio_merma = fields.Many2one('account.invoice', readonly=True, string='Folio por merma')
    folio_descuento = fields.Many2one('account.invoice', readonly=True, string='Folio por descuento')
    folio_comision = fields.Many2one('account.invoice', readonly=True, string='Folio por comision')
    folio_prontopago = fields.Many2one('account.invoice', readonly=True, string='Folio por pronto pago')

    #notascargo_diario_id=fields.Many2one(string='Diario de notas de cargo',comodel_name='account.journal')

    observaciones = fields.Text(string='Observaciones')


    
    def _compute_iva_carta(self):
        if self.invoice_id:
            if self.invoice_id.tax_line_ids:
                for tax in self.invoice_id.tax_line_ids:
                    if tax.tax_id:
                        if 'IVA' in tax.tax_id.name and 'RET' not in tax.tax_id.name:
                            self.iva = tax.amount
                            break
                        else:
                            self.iva = 0

    @api.onchange('invoice_id')
    def _onchange_r_iva_carta(self):
        if self.invoice_id:
            if self.invoice_id.tax_line_ids:
                for tax in self.invoice_id.tax_line_ids:
                    if tax.tax_id:
                        if 'IVA' in tax.tax_id.name and 'RET' in tax.tax_id.name:
                            self.r_iva = tax.amount
                            break
                        else:
                            self.r_iva = 0

    
    def _compute_r_iva_carta(self):
        if self.invoice_id:
            if self.invoice_id.tax_line_ids:
                for tax in self.invoice_id.tax_line_ids:
                    if tax.tax_id:
                        if 'IVA' in tax.tax_id.name and 'RET' in tax.tax_id.name:
                            self.r_iva = tax.amount
                            break
                        else:
                            self.r_iva = 0

    @api.model
    def create(self, vals):
        #print("****CR CREATE:"+str(vals))
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'Trafitec.Contrarecibo') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Contrarecibo') or _('Nuevo')

        self._factura_relacionada(True,vals)

        cr=super(trafitec_contrarecibo, self).create(vals)
        return cr

    #Validaciones generales.
    @api.constrains('asociado_id', 'invoice_id', 'total_g', 'subtotal_g', 'iva_g', 'r_iva_g', 'viaje_id')
    def _check_cartaporte(self):
        error = False
        errores = ""

        if self.state == 'Cancelada':
            return

        #print("**Calculos:"+str(self.totales()))

        if not self.lineanegocio:
            error = True
            errores += "Debe especificar la línea de negocio.\n"

        #if not self.viaje_id:
        #    error=True
        #    errores+="Debe especificar al menos un viaje.\n"

        #if not self.invoice_id:
        #    error=True
        #    errores+="Debe especificar la carta porte.\n"

        #facturas=self.env['acccount.invoice']

        #------------------------------------------
        #Licitación.
        #------------------------------------------
        #if self.asociado_id.para_licitacion:
        #    if not self.asociado_id.para_licitacion_aprobado:
        #        raise UserWarning(_('El asociado no esta aprobado para licitación.'))

        #Validar viajes.
        for v in self.viaje_id:
            if v.flete_asociado<=0:
                error = True
                errores += "El viaje con folio "+v.name+" no tiene calculado el flete.\n"

            if not v.documentacion_completa:
                error = True
                errores += "El viaje con folio " + v.name + " no tiene la documentación completa.\n"

            if self.invoice_id:
                if v.asociado_id.id != self.invoice_id.partner_id.id:
                    error = True
                    errores += "El viaje con folio " + v.name + " es de diferente asociado al del contra recibo.\n"

        if error:
            raise UserError(_('Alerta..\n'+str(errores)))

#Mike
class trafitec_cargospendientes(models.TransientModel):
    _name = 'trafitec.cargospendientes'
    descuento_id = fields.Integer(string="Id descuento", default=0)
    contrarecibo_id = fields.Many2one(string='Contra recibo', comodel_name='trafitec.contrarecibo')
    detalles = fields.Char(string='Detalles')
    tipo = fields.Selection(string='Tipo', selection=[(1, 'Comision'), (2, 'Descuento')])
    total = fields.Float(string='Total', default=0)
    abonos = fields.Float(string='Abonos', default=0)
    saldo = fields.Float(string='Saldo', default=0)

class trafitec_con_descuentos(models.Model):
    _name = 'trafitec.con.descuentos'

    name = fields.Char(string='Concepto',readonly=True)
    fecha = fields.Date(string='Fecha',readonly=True)
    anticipo = fields.Float(string='Anticipo',readonly=True)
    abonos = fields.Float(string='Abonos',readonly=True)
    saldo = fields.Float(string='Saldo',readonly=True)
    abono = fields.Float(string='Abono', required=True)
    folio_viaje = fields.Char(string='Folio de viaje',readonly=True)
    operador = fields.Char(string='Operador',readonly=True)
    comentarios = fields.Text(string='Comentarios',readonly=True)
    descuento_fk = fields.Many2one('trafitec.descuentos',string='Id del descuento',required=True)
    linea_id = fields.Many2one(comodel_name="trafitec.contrarecibo", string="Contrarecibo id", ondelete='cascade')
    viaje_id = fields.Many2one('trafitec.viajes',string='Viaje ID')

    
    def _compute_cobrado(self):
        if self.linea_id.state != 'Nueva' :
            if self.linea_id.cobrar_descuentos == 'No cobrar':
                self.cobrado = False
            if self.linea_id.cobrar_descuentos == 'Todos':
                self.cobrado = True
            if self.linea_id.cobrar_descuentos == 'Viajes del contrarecibo':
                for viaje in self.linea_id.viaje_id:
                    if self.viaje_id.id == viaje.id:
                        self.cobrado = True
                        break
                    else:
                        self.cobrado = False
        else:
            self.cobrado = False
    cobrado = fields.Boolean(string='Cobrado', default=False, compute='_compute_cobrado')


    @api.onchange('abono')
    def _onchange_abono(self):
        if self.abono > self.saldo:
            self.abono = self.saldo
            res = {'warning': {
                'title': _('Advertencia'),
                'message': _('No puede poner un monto mayor de abono al saldo faltante.')
            }}
            return res

    @api.constrains('abono')
    def _check_abono(self):
        if self.abono <= 0:
            raise UserError(_(
                'Aviso !\nEl monto del abono debe ser mayor a cero.'))

class trafitec_con_comision(models.Model):
    _name = 'trafitec.con.comision'

    name = fields.Char(string='Folio del viaje', readonly=True)
    fecha = fields.Date(string='Fecha', readonly=True)
    comision = fields.Float(string='Comision', readonly=True)
    abonos = fields.Float(string='Abonos', readonly=True)
    saldo = fields.Float(string='Saldo', readonly=True)
    asociado_id = fields.Many2one('res.partner', string="Asociado", domain="[('asociado','=',True)]", readonly=True)
    tipo_viaje = fields.Char(string='Tipo de viaje', readonly=True)
    cargo_id = fields.Many2one('trafitec.cargos',string='ID comision')
    line_id = fields.Many2one(comodel_name="trafitec.contrarecibo", string="Contrarecibo id", ondelete='cascade')
    viaje_id = fields.Many2one('trafitec.viajes', string='Viaje ID')
    cobrado = fields.Boolean(string='Cobrado', default=False)

#Descuentos por cobrar.
class trafitec_contrarecibo_descuentosx(models.TransientModel):
    _name = 'trafitec.contrarecibos.descuentosx'
    descuento_id=fields.Many2one(comodel_name='trafitec.descuentos',string='Descuentos')
    concepto=fields.Char(string='Concepto', default='')
    total=fields.Float(string='Total', default=0)
    abonos=fields.Float(string='Abonos', default=0)
    saldo=fields.Float(string='Saldo', default=0)
    abono=fields.Float(string='Abono', default=0)
    
class viajesxcontrarecibo(models.Model):
    _name='trafitec.viajesxcontrarecibo'
    viaje_id=fields.Many2one(string='Viaje', comodel_name='trafitec.viajes')
    contrarecibo_id=fields.Many2one(string='Contra recibo', comodel_name='trafitec.contrarecibo')
    factura_id=fields.Many2one(string='Factura', comodel_name='account.invoice')

    @api.model
    def create(self, vals):
        viaje = self.env['trafitec.viajes'].search([('id', '=', vals['viaje_id'])])
        viaje.write({'en_contrarecibo': True, 'factura_proveedor_id': vals['factura_id']})
        return super(viajesxcontrarecibo, self).create(vals)
    
    
    def unlink(self):
        for reg in self:
            viaje=self.env['trafitec.viajes'].search([('id', '=', reg.viaje_id.id)])
            viaje.write({'en_contrarecibo':False, 'factura_proveedor_id':False})
        return super(viajesxcontrarecibo, self).unlink()

class trafitec_contrarecibos_cargos(models.Model):
    _name = 'trafitec.contrarecibos.cargos'
    tipo_cargo_id = fields.Many2one(
        string='Tipo de cargo adicional',
        comodel_name='trafitec.tipocargosadicionales',
        required=True
    )
    valor = fields.Float(
        string='Valor',
        default=0,
        required=True
    )
    contrarecibo_id = fields.Many2one(
        string='Contra recibo',
        comodel_name='trafitec.contrarecibo'
    )

    viaje_id = fields.Many2one(
        string='Viaje',
        comodel_name='trafitec.viajes'
    )
