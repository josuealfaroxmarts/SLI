from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    plazas_ban_id = fields.Many2one(
        'trafitec.plazas.banxico',
        string='Plaza:'
    )
    no_sucursal = fields.Char(string='No. de sucursal')
