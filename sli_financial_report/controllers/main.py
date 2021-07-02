# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import base64
import werkzeug


class BinaryDownloadController(http.Controller):
	@http.route('/web/binary/download', type='http', auth="public")
	@serialize_exception

	def download(self, model, field, id, filename=None, **kw):
		Model = request.env[model].sudo().search([('id', '=', int(id))])
		filecontent = base64.b64decode(Model.file or '')
		headers = werkzeug.datastructures.Headers()
		
		if not filecontent:
			return request.not_found()
		else:
			if not filename:
				filename = '%s_%s' % (model.replace('.', '_'), id)
				headers.add('Content-Disposition', 'attachment', filename=filename)
				return request.make_response(filecontent,headers)
			else:
				headers.add('Content-Disposition', 'attachment', filename=filename)
				return request.make_response(filecontent,headers)