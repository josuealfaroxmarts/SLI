# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class FeeReport(models.Model):
    _name = "fee.report"
    _description = "Fee Report"
    _auto = False

    id = fields.Integer(readonly=True)
    name = fields.Char(readonly=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True
    )
    state = fields.Char(readonly=True)

    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, "fee_report")
        self._cr.execute(
            """ CREATE VIEW fee_report AS (
                    select
                    id as id,
                    name as name,
                    partner_id as partner_id,
                    state as state
                    from account_move
                    limit 5
                )
            """
        )
