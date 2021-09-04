from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError, RedirectWarning


class TrafitecViajes(models.Model):
    _inherit = 'trafitec.viajes'
    
    asignadoi_id = fields.Many2one(
        string='Intentando asignar a', 
        comodel_name='res.users', 
        help='Usuario al que se intenta asignar el viaje.'
    )
    asignacion_id = fields.Many2one(
        string='Asignación', 
        comodel_name='sli.seguimiento.registro', 
        help='Asignación'
    )
    
    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        for viaje in self:
	        if self.asignacion_id:
	            self.asignacion_id.state = 'descartado'
	            self.asignacion_id.fechahora_ar = datetime.now()

	        self.with_context(validar_credito_cliente=False).write({
		        'asignacion_id': False,
		        'asignadoa_id': False,
		        'asignadoi_id': False})

    def action_intento_quitar(self):
        """Quita la asignacion incondicionalmente."""
        for viaje in self:
	        if self.asignacion_id:
	            self.asignacion_id.state = 'descartado'
	            self.asignacion_id.fechahora_ar = datetime.now()

	        self.asignacion_id = False
	        self.asignadoa_id = False
	        self.asignadoi_id = False

    def action_asignar_asignar(self):
        """Asignación."""
        if self.asignadoa_id:
            if self.asignadoa_id.id != self.env.user.id:
                raise UserError(_('Para poder asignar el viaje, este viaje debe estar asignado a usted.'))

        if self.asignadoi_id:
           raise UserError(_('Para poder asignar el viaje no debe haber intento de asignación.'))

        
        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_viaje_form').id
        viaje_id = self.id
        
        return {
            'name': _('Asignar viaje '+(self.name or '')),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': {'default_viaje_id': viaje_id, 'default_tipo': 'viaje'}
        }