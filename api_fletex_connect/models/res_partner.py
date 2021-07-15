# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class fletex_respartner(models.Model):
    _inherit = 'res.partner'

    id_fletex = fields.Integer(string='ID Fletex')
    send_to_api = fields.Boolean(default=False)
    driver_id_fletex = fields.Integer()
    legal_representative = fields.Char(string='Representante legal')
    status_fletex = fields.Selection([('incomplete', 'No completado'), 
                                        ('completed', 'Completado')],
                                        string='Estado en Fletex', 
                                        readonly=True, 
                                        default='incomplete')
    rfc = fields.Binary(string="RFC")
    date_born = fields.Date(string="Fecha de nacimiento")
    progress_fletex = fields.Float(string="Progreso en Fletex", default="0.0")
    step_one = fields.Boolean(
        string='Informacion de la empresa',
    )
    step_two = fields.Boolean(
        string='Localizaciones',
    )
    step_three = fields.Boolean(
        string='Terminos y condiciones',
    )
    step_truck = fields.Boolean(
        string='Vehiculos',
    )

    step_operator = fields.Boolean(
        string='Operadores',
    )

    #fields for the legal representative
    name_representative = fields.Char(string="Nombre(s)")
    lastname_representative = fields.Char(string="Apellido(s)")
    email_representative = fields.Char(string="Correo Electronico")
    phone_representative = fields.Char(string="Teléfono de contacto")
    name_id_representative = fields.Char(compute="change_name")
    ext_id_representative = fields.Char(string="Extension Identificacion Fisica")
    id_representative = fields.Binary(string="Identificacion del representante")
    id_approved = fields.Boolean(string='Identificacion aprobada')
    rfc_representative = fields.Char(string="RFC del representante")
    rfc_representative_drop = fields.Binary(string="RFC del representante ")
    rfc_representative_drop_approved = fields.Boolean(string='RFC representante Aprobado')
    name_rfc_representative_drop = fields.Char(compute='change_name')
    ext_representative_drop = fields.Char(string="RFC del representante")
    name_act_representative = fields.Char(compute="change_name")
    ext_act_representative = fields.Char(string="extension acta moral")
    act_representative = fields.Binary(string="Acta constitutiva / Boleta registral")
    act_approved = fields.Boolean(string='Acta constitutiva aprobada')
    name_address_representative = fields.Char(compute="change_name")
    ext_address_representative = fields.Char(string="Extension domicilio moral")
    address_representative = fields.Binary(string="Comprobante de domilicio fiscal")
    address_approved = fields.Boolean(string='Comprobante de domilicio fiscal Aprovado')
    name_rfc_bussiness = fields.Char(compute='change_name')
    ext_rfc_bussiness = fields.Char()
    rfc_bussiness = fields.Binary(string="RFC Empresa")
    rfc_approved = fields.Boolean(string='RFC Empresa Aprobado')
    vat_info = fields.Char(string='vat')
    status_record = fields.Selection(
                                    [('draft', 'pending'),
                                    ('pending', 'Pendiente'),
                                    ('approved', 'Aprobado'),
                                    ('refused', 'Rechazado')],
                                    string='Estado', 
                                    readonly=True, 
                                    default='draft')
    status_document = fields.Boolean()
    limit_credit = fields.Float('Limite de credito')
    limit_credit_fletex = fields.Float('Limite de credito en FLETEX')
    balance_invoices = fields.Float('Saldo en facturas')

    def change_name(self):
        if self.name:
            self.name_license_driver = "Licencia de {}.{}".format(
                                    self.name, 
                                    self.ext_license_driver)
            self.name_id_representative = "Identificacion del representante de {}.{}".format(
                                    self.name, 
                                    self.ext_id_representative)
            self.name_act_representative = "Acta constitutiva del representante de {}.{}".format(
                                    self.name, 
                                    self.ext_act_representative)
            self.name_address_representative = "Comprobante del domicilio del representante de {}.{}".format(
                                    self.name, 
                                    self.ext_address_representative)
            self.name_rfc_bussiness = "RFC de {}.{}".format(
                                    self.name, 
                                    self.ext_rfc_bussiness)
            self.name_rfc_representative_drop = "RFC de {} {}.{}".format(
                                    self.name_representative, 
                                    self.lastname_representative, 
                                    self.ext_representative_drop)
            self.name_healthcare_number = "Numero de seguro social de {}.{}".format(
                                    self.name, 
                                    self.ext_healthcare_number)

    def approve_status_email(self):		
        if self.status_record == 'approved' and self.customer == True:
            for rec in self :
                rec.status_record = 'approved'
                template_id = self.env.ref('sli_trafitec.account_approve').id
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
        elif self.status_record == 'refused':
            for rec in self :
                rec.status_record = 'refused'
                template_id = self.env.ref('sli_trafitec.account_refuse').id
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
        elif self.status_record == 'approved' and self.supplier == True:
            for rec in self :
                template_id = self.env.ref('sli_trafitec.account_approve').id
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
        elif self.operador == True:
            for rec in self:
                rec.status_record = 'approved'
        else :
            for rec in self :
                rec.status_record = 'pending'

    def approve_documents(self):
        self.status_document = True

    def refuse_status(self):
        self.send_to_api = False
        self.status_user = True
        self.status_record = "refused"
        self.approve_status_email()


    def approve_status(self):
        if self.status_document:		
            if self.limit_credit <= 0 and self.customer == True :
                raise UserError(_('Aviso !\n El límite de crédito debe ser mayor a 0.'))
            else :
                self.send_to_api = False
                self.status_record = "approved"
                self.approve_status_email()
        else :
            raise UserError(_('Aviso !\n Debe aprobar los documentos primero.'))

    @api.onchange('status_record')
    def _verify_limit_credit(self):
        if self.operador == False:
            if self.status_record == 'approved' and self.customer == True:
                if self.limit_credit <= 0:
                    raise UserError(
                _('Aviso !\n El limite de credito debe ser mayor a 0.'))
    	
    @api.onchange('status_record')
    def _verify_limit_credit(self):
        if self.operador == False:
            if self.status_record == 'approved' and self.customer == True:
                if self.limit_credit <= 0:
                    raise UserError(
                _('Aviso !\n El limite de credito debe ser mayor a 0.'))

    @api.onchange('limit_credit')
    def change_limits(self):
        self.limit_credit_fletex = self.limit_credit - self.balance_invoices
