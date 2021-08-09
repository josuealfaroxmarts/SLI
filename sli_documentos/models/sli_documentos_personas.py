from odoo import api, fields, models

class SliDocumentosPersonas(models.Model):
    _name = 'sli.documentos.personas'
    _description ='SLI documentos personas'
    
    documento_id = fields.Many2one(
        string='Documento', 
        comodel_name='sli.documentos.documentos', 
        help='Documento relacionado'
    )
    persona_id = fields.Many2one(
        string='Persona', 
        comodel_name='res.partner', 
        help='Persona relacionada'
    )