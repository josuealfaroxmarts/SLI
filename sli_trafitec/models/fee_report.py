from odoo import api, models, fields, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class ReportFee(models.Model):
    _name = 'fee.report'
    _description ='fee report'
    _auto = False

    id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', 
        string='Partner', 
        readonly=True
    )
    state = fields.Char(readonly=True)

    def init(self):

        ''' Event Question main report '''
        tools.drop_view_if_exists(self._cr, 'fee_report')
        self._cr.execute(
            ''' CREATE VIEW fee_report AS (
                    select
                    f.id id,
                    f.name name,
                    f.partner_id partner_id,
                    f.state state
                    from account_invoice f
                    limit 5
                )
            '''
        )
