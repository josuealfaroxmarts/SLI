from odoo import models, fields, api, exceptions, tools

class usuarios(models.Model):
    _name='sli.portales.usuarios'
    name=fields.Char(string="Usuario",required=True, default='')
    clave=fields.Char(string="Clave",required=True, default='')
    nombrecompleto=fields.Char(string="Nombre completo", required=True, default='')
    es_cliente=fields.Boolean(string="Es cliente", default=False)
    es_asociado=fields.Boolean(string="Es asociado", default=False)
    persona_id=fields.Many2one(string="Persona", comodel_name='res.partner', required=True)
    tipo=fields.Selection(string="Tipo", selection=[('administrador', 'Administrador'), ('gps', 'GPS'),('operativo','Operativo')], required=True)
    st=fields.Boolean(string="Activo", default=True)
    registros_id = fields.One2many(string='Registro', comodel_name='sli.portales.registro', inverse_name='usuario_id')
    empresa_id = fields.Many2one(string='Empresa', comodel_name='res.company', default=lambda self: self.env['res.company']._company_default_get('sli.portales.usuarios'))
   
    
    def action_borrar_registros(self):
        try:
            for r in self.registros_id:
                r.unlink()
        except():
            raise UserWarning("Error al borrar los registro.")
   
class usuarios_log(models.Model):
    _name = 'sli.portales.registro'
    usuario_id = fields.Many2one(string='Usuario', comodel_name='sli.portales.usuarios')
    detalles = fields.Char(string='Detalles', default='')
    

