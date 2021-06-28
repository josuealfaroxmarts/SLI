## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


"""
TRAFITEC GLO
Clase de utileria general del sistema.
"""
class trafitec_glo(models.Model):
	_name = 'trafitec.glo'
	_auto = False
	
	
	def cfg(self):
		emp = None
		emp = self.env['res.company']._company_default_get('sli_trafitec')
		cfg = self.env['trafitec.parametros'].search([('company_id', '=', emp.id)])
		return cfg
	
	"""Regresa Todos los viajes del asociado de acuerdo al municipio origen y destino."""
	def ViajesAsociadoPorMunicipios(self, asociado_id=None, municipio_origen_id=None, municipio_destino_id=None):
		if not asociado_id or not municipio_origen_id or not municipio_destino_id:
			return []
		
		lista = []
		sql = """
select
v.id id,
v.name folio,
aso.name asociado,
ori.name origen,
des.name destino,
v.tarifa_asociado tarifa
from trafitec_viajes as v
  inner join trafitec_ubicacion as ori on(v.origen=ori.id)
  inner join trafitec_ubicacion as des on(v.destino=des.id)
  inner join res_partner as aso on(v.asociado_id=aso.id)
where
v.state='Nueva'
and v.asociado_id = {}
and ori.municipio = {}
and des.municipio = {}

order by v.tarifa_asociado asc
""".format(asociado_id, municipio_origen_id, municipio_destino_id)
		self.env.cr.execute(sql)
		lista = self.env.cr.dictfetchall()
		return lista

	def SeguridadDerecho(self, derecho_id=0):
		return True
	
	def enviar_correo(self, para='', asunto='', contenido=''):
		valores = {
			'subject': asunto,
			'body_html': contenido,
			'email_to': para,
			'email_cc': ';',
			'email_from': 'info@sli.mx',
		}
		create_and_send_email = self.env['mail.mail'].create(valores).send()
