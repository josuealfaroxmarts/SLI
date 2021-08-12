# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
import datetime
from datetime import timedelta


class TrafitecCrmTraficoTablero(models.Model):
    _name = "trafitec.crm.trafico.tablero"
    _description = 'crm trafico tablero'

    name = fields.Char(string="Nombre")
    color = fields.Integer(string='Color')
    cotizaciones_disponibles_n = fields.Integer(
        string="Cotizaciones disponibles",
        compute="_compute_cotizaciones_disponibles_n",
        store=False
    )
    misviajes_n = fields.Integer(
        string="Mis viajes recientes",
        compute="_compute_misviajes_n",
        store=False
    )
    misviajeshoy_n = fields.Integer(
        string="Mis viajes hoy",
        compute="_compute_misviajeshoy_n",
        store=False
    )
    misviajesc_n = fields.Integer(
        string="Mis viajes cancelados",
        compute="_compute_misviajesc_n",
        store=False
    )

    def _compute_cotizaciones_disponibles_n(self):
        for rec in self:
            n = self.env['trafitec.cotizacion'].search([
                ('state', '=', 'Disponible')
            ])
            rec.cotizaciones_disponibles_n = len(n)

    def _compute_misviajeshoy_n(self):
        for rec in self:
            n = self.env['trafitec.viajes'].search_count([
                ('state', '=', 'Nueva'),
                ('create_uid', '=', self.env.user.id),
                ('create_date', '>=', str(datetime.datetime.today().date()))
            ])
            rec.misviajeshoy_n = n

    def _compute_misviajes_n(self):
        for rec in self:
            n = self.env['trafitec.viajes'].search_count([
                ('state', '=', 'Nueva'),
                ('create_uid', '=', rec.env.user.id),
                (
                    'create_date',
                    '>=',
                    (
                        datetime.date.today()
                        + timedelta(days=-7)
                    ).strftime("%Y-%m-%d")
                )
            ])
            rec.misviajes_n = n

    def _compute_misviajesc_n(self):
        for rec in self:
            n = self.env['trafitec.viajes'].search_count([
                ('state', '!=', 'Nueva'),
                ('create_uid', '=', self.env.user.id)
            ])
            rec.misviajesc_n = n

    def action_abrir_crm_cotizaciones(self):
        return {
            'name': 'CRM Tráfico',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.crm.trafico',
            'target': 'current',
            'multi': True,
            'context': self._context,
        }

    def action_abrir_crm_viajes(self):
        return {}

    def action_abrir_cotizaciones(self):
        return {
            'name': 'Mis cotizaciones (' + (self.env.user.name or '') + ')',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.cotizacion',
            'context': {},
            'domain': [('create_uid', '=', self.env.user.id)]
        }

    def action_abrir_viajes(self):
        return {
            'name': 'Mis viajes (' + (self.env.user.name or '') + ')',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'trafitec.viajes',
            'context': {},
            'domain': [('create_uid', '=', self.env.user.id)]
        }
