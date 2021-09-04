from datetime import datetime, date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SliDocumentosDocumentos(models.Model):
    _name = 'sli.documentos.documentos'
    _description = 'SLI documentos'

    @api.depends('fecha_final')
    def compute_dias_para_vencimiento(self):
        fecha_final = datetime.strptime(self.fecha_final, "%Y-%m-%d").date()
        self.dias_para_vencimiento = (fecha_final - date.today()).days
    
    name = fields.Char(
        string='Nombre', 
        help='Nombre del documento'
    )
    folio = fields.Char(
        string='Folio', 
        help='Folio del documento'
    )
    fecha = fields.Date(
        string='Fecha del documento', 
        help='Fecha del documento.'
    )
    persona_id = fields.Many2one(
        string='Persona relacionada', 
        comodel_name='res.partner', 
        help='Persona relacionada.'
    )
    empleado_id = fields.Many2one(
        string='Empleado relacionado', 
        comodel_name='hr.employee', 
        help='Empleado relacionado.'
    )
    vehiculo_id = fields.Many2one(
        string='Vehiculo relacionado', 
        comodel_name='fleet.vehicle', 
        help='Vehiculo relacionado.'
    )
    fecha_inicial = fields.Date(
        string='Fecha inicial de documento', 
        help='Fecha de vigencia inicial del documento.'
    )
    fecha_final = fields.Date(
        string='Fecha final de documento', 
        help='Fecha de vigencia final del documento.'
    )
    detalles = fields.Text(
        string='Detalles del documento', 
        help='Detalles especificos del documento'
    )
    tipo = fields.Selection(
        string='Tipo', 
        selection=[
            ('noespecificado', '(No especificado)'), 
            ('licencia', 'Licencia'), 
            ('contrato', 'Contrato'), 
            ('otro', 'Otro')], 
        default='noespecificado'
    )
    personas_ids = fields.One2many(
        string='Personas a notificar', 
        comodel_name='sli.documentos.personas', 
        inverse_name='documento_id', 
        help='Personas relacionadas a notificar'
    )
    version = fields.Integer(
        string='Versión', 
        default=1, 
        help='Versión del documento.'
    )
    notificar_dias = fields.Integer(
        string='Notificar faltando', 
        default=7, 
        help='Indica los dias en que se iniciaran las'
             ' notificaciones antes de la fecha final'
    )
    notificar_frecuencia = fields.Integer(
        string='Notificar frecuencia', 
        default=1, 
        help='Frecuencia de notificaciones.'
    )
    notificar_fechahorau = fields.Datetime(
        string='Notificar fecha y hora de ultima notificacion', 
        help='Fecha y hora de ultima notificacion.'
    )
    state = fields.Selection(
        string='Estado', 
        selection=[
            ('vigente', 'Vigente'), 
            ('vencido', 'Vencido')], 
        default='vigente', 
        help='Indica el estado del documento establecido manualmente.'
    )
    dias_para_vencimiento = fields.Integer(
        string='Días para vencimiento', 
        compute=compute_dias_para_vencimiento, 
        store=True, 
        help='Días para vencimiento.'
    )
    active = fields.Boolean(
        string='Activo', 
        default=True
    )
    archivo_nombre = fields.Char(
        "Nombre archivo", 
        default='datos.txt'
    )
    archivo_datos = fields.Binary()

    def action_servicio_notificaciones(self):
        """Obtener todos los documentos vigentes."""

        hoy = date.today()
        for d in self.filtered(lambda x: x.state == 'vigente'):
            notificar = False
            fecha_final = datetime.strptime(d.fecha_final, "%Y-%m-%d").date()
            dias = ( fecha_final - hoy).dif.days
            #Actualiza el estado del documento.
            if dias <= 0:
                d.state = 'vencido'
                continue
            #Verifica si esta por vencer.
            if dias <= d.notificar_dias:
                if d.notificar_fechahorau:
                    fecha_final_un = datetime.strptime(
                        d.notificar_fechahorau, "%Y-%m-%d %H:%M:%S").date()
                    dias_un = (hoy - fecha_final_un).days
                    if dias_un >= 1:
                        notificar = True
                else:
                    notificar = True
                #Notificar.
                if notificar:
                    d.notificar_fechahorau = hoy
                    mensaje = "Faltan {} dias para vencimiento de" \
                              " {} con folio {}.".format(dias, d.name, d.folio)
                    for p in d.personas_ids:
                        if p.persona_id.email:
                            vals = {
                                'subject': 'Vigencia',
                                'body_html': mensaje,
                                'email_to': p.persona_id.email or '',
                                'email_cc': '',
                                'email_from': 'info@sli.mx',
                            }
                            self.env['mail.mail'].create(vals)

    @api.constrains('notificar_dias', 'notificar_frecuencia')
    def valida(self):
        error = False
        errores = ''
        if not self._context.get('validar', True):
            return
        if self.fecha_inicial > self.fecha_final:
            error = True
            errores += "La fecha inicial debe ser menor a la fecha final.\n"
        if self.notificar_dias <= 0:
            error = True
            errores += 'Los dias para la notificación debe ser mayor a cero.\n'
        if self.notificar_frecuencia <= 0:
            error = True
            errores += 'La frecuencia para la notificación debe ser mayor a cero.\n'
        if error:
            raise ValidationError(_(errores))