from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
	_inherit = "res.partner"

	id_fletex = fields.Integer(string="ID Fletex")
	send_to_api = fields.Boolean(default=False)
	driver_id_fletex = fields.Integer()
	legal_representative = fields.Char(string="Representante legal")
	status_fletex = fields.Selection(
		[
			("incomplete", "No completado"),
			("completed", "Completado")
		],
		string="Estado en Fletex",
		readonly=True,
		default="incomplete"
	)
	rfc = fields.Binary(string="RFC")
	date_born = fields.Date(string="Fecha de nacimiento")
	progress_fletex = fields.Float(
		string="Progreso en Fletex",
		default="0.0"
	)
	step_one = fields.Boolean(string="Informacion de la empresa")
	step_two = fields.Boolean(string="Localizaciones")
	step_three = fields.Boolean(string="Terminos y condiciones")
	step_truck = fields.Boolean(string="Vehiculos")
	step_operator = fields.Boolean(string="Operadores")
	name_representative = fields.Char(string="Nombre(s)")
	lastname_representative = fields.Char(string="Apellido(s)")
	email_representative = fields.Char(string="Correo Electronico")
	phone_representative = fields.Char(string="Teléfono de contacto")
	name_id_representative = fields.Char(compute="change_name")
	ext_id_representative = fields.Char(
		string="Extension Identificacion Fisica"
	)
	id_representative = fields.Binary(
		string="Identificacion del representante"
	)
	id_approved = fields.Boolean(string="Identificacion aprobada")
	rfc_representative = fields.Char(string="RFC del representante")
	rfc_representative_drop = fields.Binary(string="RFC del representante")
	rfc_representative_drop_approved = fields.Boolean(
		string="RFC representante Aprobado"
	)
	name_rfc_representative_drop = fields.Char(compute="change_name")
	ext_representative_drop = fields.Char(string="RFC del representante")
	name_act_representative = fields.Char(compute="change_name")
	ext_act_representative = fields.Char(string="extension acta moral")
	act_representative = fields.Binary(
		string="Acta constitutiva / Boleta registral"
	)
	act_approved = fields.Boolean(string="Acta constitutiva aprobada")
	name_address_representative = fields.Char(compute="change_name")
	ext_address_representative = fields.Char(
		string="Extension domicilio moral"
	)
	address_representative = fields.Binary(
		string="Comprobante de domilicio fiscal"
	)
	address_approved = fields.Boolean(
		string="Comprobante de domilicio fiscal Aprobado"
	)
	name_rfc_bussiness = fields.Char(compute="change_name")
	ext_rfc_bussiness = fields.Char()
	ext_license_driver = fields.Char()
	rfc_bussiness = fields.Binary(string="RFC Empresa")
	rfc_approved = fields.Boolean(string="RFC Empresa Aprobado")
	vat_info = fields.Char(string="vat")
	status_record = fields.Selection(
		[
			("draft", "pending"),
			("pending", "Pendiente"),
			("approved", "Aprobado"),
			("refused", "Rechazado")
		],
		string="Estado",
		readonly=True,
		default="draft"
	)
	status_document = fields.Boolean()
	limit_credit = fields.Float(string="Límite de credito")
	limit_credit_fletex = fields.Float(string="Límite de credito en Fletex")
	balance_invoices = fields.Float(string="Saldo en facturas")

	def change_name(self):
		for partner in self:
			if not self.name:
				return
			partner.name_license_driver = "Licencia de {}.{}".format(
				partner.name, partner.ext_license_driver
			)
			partner.name_id_representative = (
				"Identificacion del representante de {}.{}".format(
					partner.name, partner.ext_id_representative
				)
			)
			partner.name_act_representative = (
				"Acta constitutiva del representante de {}.{}".format(
					partner.name, partner.ext_act_representative
				)
			)
			partner.name_address_representative = (
				"Comprobante del domicilio del representante de {}.{}".format(
					partner.name, partner.ext_address_representative
				)
			)
			partner.name_rfc_bussiness = (
				"RFC de {}.{}".format(
					partner.name, partner.ext_rfc_bussiness
				)
			)
			partner.name_rfc_representative_drop = (
				"RFC de {} {}.{}".format(
					partner.name_representative,
					partner.lastname_representative,
					partner.ext_representative_drop
				)
			)
			partner.name_healthcare_number = (
				"Numero de seguro social de {}.{}".format(
					partner.name, partner.ext_healthcare_number
				)
			)

	def approve_status_email(self):
		for partner in self:
			if partner.status_record == "approved":
				for rec in self:
					rec.status_record = "approved"
					template_id = self.env.ref("sli_trafitec.account_approve").id
					self.env["mail.template"].browse(template_id).send_mail(
						partner.id, force_send=True
					)
			elif partner.status_record == "refused":
				for rec in self:
					rec.status_record = "refused"
					template_id = self.env.ref("sli_trafitec.account_refuse").id
					self.env["mail.template"].browse(template_id).send_mail(
						self.id, force_send=True)
			elif partner.status_record == "approved":
				for rec in self:
					template_id = self.env.ref("sli_trafitec.account_approve").id
					self.env["mail.template"].browse(template_id).send_mail(
						self.id, force_send=True)
			elif partner.operador:
				for rec in self:
					rec.status_record = "approved"
			else:
				for rec in self:
					rec.status_record = "pending"

	def approve_documents(self):
		self.status_document = True

	def refuse_status(self):
		self.send_to_api = True
		self.status_user = True
		self.status_record = "refused"
		self.approve_status_email()

	def approve_status(self):
		for partner in self:
			if partner.status_document:
				if (
						partner.limit_credit <= 0
						and partner.customer_rank >= 1
						and not partner.operador
				):
					raise UserError(
						_("Aviso !\n El límite de crédito debe ser mayor a 0."))
				else:
					partner.send_to_api = True
					partner.status_record = "approved"
					partner.approve_status_email()
			else:
				raise UserError(
					_("Aviso !\n Debe aprobar los documentos primero."))

	@api.onchange("status_record")
	def _verify_limit_credit(self):
		for partner in self:
			if not partner.operador:
				if (
						partner.status_record == "approved"
						and partner.customer_rank >= 1
				):
					if partner.limit_credit <= 0:
						raise UserError(
							_("Aviso !\n El limite de credito debe ser mayor a 0."))

	@api.onchange("limit_credit")
	def _onchange_limits(self):
		for partner in self:
			partner.limit_credit_fletex = (
					partner.limit_credit
					- partner.balance_invoices
			)
