
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    asignadoa_id = fields.Many2one(
        string='Asignado a', 
        comodel_name='res.users',
        help='Usuario que tiene asignada la factura.'
    )
    asignadoi_id = fields.Many2one(
        string='Intentando asignar a', 
        comodel_name='res.users', 
        help='Usuario al que se intenta asignar la factura.'
    )
    asignacion_id = fields.Many2one(
        string='Asignación', 
        comodel_name='sli.seguimiento.registro', 
        help='Asignación'
    )

    def action_asignar_quitar(self):
        """Quita la asignacion incondicionalmente."""
        for move in self:
            if move.asignacion_id:
                move.asignacion_id.state = 'descartado'
                move.asignacion_id.fechahora_ar = datetime.now()
            move.asignacion_id = False
            move.asignadoa_id = False
            move.asignadoi_id = False
            move.asignadoa_id = False

    def action_asignar_asignar(self):
        """Asignación Wizard."""
        for move in self:
            if move.asignadoa_id:
                if move.asignadoa_id.id != self.env.user.id:
                    raise ValidationError(_(
                        'Para poder asignar la factura, esta factura '
                        'debe estar asignado a usted.'))
            if move.asignadoi_id:
               raise ValidationError(_(
                   'Para poder asignar la factura no debe '
                   'haber intento de asignación.'))

            view_id = self.env.ref(
                'sli_documentos.sli_seguimeinto_asignar_factura_form').id
            factura_id = move.id

            return {
                'name': _('Asignar factura '+ (move.number or '')),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sli.seguimiento.asignar',
                'view_id': view_id,
                'target': 'new',
                'context': {
                    'default_factura_id': factura_id,
                    'default_tipo': 'factura'}
            }