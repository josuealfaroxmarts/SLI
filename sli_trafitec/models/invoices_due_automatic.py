# -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
from xml.dom import minidom

import base64
_logger = logging.getLogger(__name__)


class InvoiceDueAutomatic(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def run_revision_due_invoices(self, id=None):
        domain = [('date_due', '=', fields.Date.today()),
                  ('state', '=', 'open'),('partner_id.customer', '=', True)]
        print(domain)
        for invoice in self.search(domain):
            print('Entro en el for')
            saldo = invoice.partner_id.saldo_facturas + invoice.amount_total
            saldo_restante = invoice.partner_id.limite_credito - saldo
            invoice.partner_id.write(
                {'saldo_facturas': saldo, 'limite_credito_fletex': saldo_restante})
            print('se termino el for')
