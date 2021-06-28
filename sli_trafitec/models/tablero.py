## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import xlrd
import shutil
import logging
_logger = logging.getLogger(__name__)

class trafitec_tablero(models.Model):
    _name = 'trafitec.tablero'
