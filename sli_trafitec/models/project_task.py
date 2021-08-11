# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    bloquear_fechalimite = fields.Boolean(
        string='Bloquear fecha limite',
        default=False
    )

    @api.model
    def create(self, vals):
        vals['bloquear_fechalimite'] = True

        return super(ProjectTask, self).create(vals)
