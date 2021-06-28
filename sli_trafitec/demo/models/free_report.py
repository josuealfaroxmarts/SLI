## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging

_logger = logging.getLogger(__name__)

class ReportFee(models.Model):
    _name = 'fee.report'
    _auto = False

    id = fields.Integer(readonly=True)
    number = fields.Char(readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True)
    state = fields.Char(readonly=True)

    @api.multi
    def button_create_inv(self):
        print('OK')

    @api.model_cr
    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'fee_report')
        self._cr.execute(""" CREATE VIEW fee_report AS (
                    select
                    f.id id,
                    f.number number,
                    f.partner_id partner_id,
                    f.state state
                    from account_invoice f
                    limit 5
        )""")
