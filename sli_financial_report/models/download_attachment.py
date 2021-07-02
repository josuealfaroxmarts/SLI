# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

import ntpath
import os
import shutil
import tarfile
from random import randint
import logging
_logger = logging.getLogger(__name__)

from odoo import _, api, exceptions, fields, models


class DownloadAttachment(models.Model):

	_name = "download.attachment"


	file = fields.Binary(
		readonly=True,
		string=_("Archivo")
	)

	filename = fields.Char(
		string=_("Nombre del archio")
	)

	active_model = fields.Char(
		string=_("Modelo")
	)
	active_id = fields.Char(
		string=_("ID Activo")
	)

	attachment_ids = fields.Many2many(
		'ir.attachment', 
		string=_("Adjuntos")
	)


	# 
	# def download_attachment(self):
	# 	config_obj = self.env['ir.config_parameter']

	# 	invoice_ids = self._context.get('active_ids')
	# 	attachment_obj = self.env['ir.attachment'].search([('res_id', 'in', invoice_ids), ('res_model', '=', 'account.move')])
	# 	active_ids = []
	# 	for att in attachment_obj:
	# 		active_ids.append(att.id)

	# 	attachment_ids = active_ids
	# 	ids = self._ids

	# 	filestore_path = os.path.join(attachment_obj._filestore(), '')
	# 	attachment_dir = filestore_path + 'Adjuntos'

	# 	if not os.path.exists(attachment_dir):
	# 		os.makedirs(attachment_dir)
	# 	else:
	# 		shutil.rmtree(attachment_dir)
	# 		os.makedirs(attachment_dir)

	# 	file_name = 'Adjuntos'

	# 	if isinstance(ids, int):
	# 		ids = [ids]

	# 	wzrd_obj = self
	# 	config_ids = config_obj.search([('key', '=', 'web.base.url')])
	# 	self.env['ir.attachment'].search([('active','=',False)]).unlink()

	# 	if len(config_ids):
	# 		value = config_ids[0].value
	# 		active_model = 'ir.attachment'
	# 		active_id = wzrd_obj.id			
	# 		tar_dir = os.path.join(attachment_dir, file_name)
	# 		tFile = tarfile.open(tar_dir, 'w:gz')

	# 		if value and active_id and active_model:
	# 			original_dir = os.getcwd()
	# 			filter_attachments = []

	# 			for attach in attachment_obj.browse(attachment_ids):
	# 				if attach.active:
	# 					filter_attachments.append(attach.id)

	# 			if not filter_attachments:
	# 				raise exceptions.UserError(_("Ńo hay archivos que descargar"))

	# 			for attachment in attachment_obj.browse(filter_attachments):
	# 				full_path = attachment_obj._full_path(attachment.store_fname)
	# 				attachment_name = attachment.datas_fname
	# 				new_file = os.path.join(attachment_dir, attachment_name)
					
	# 				try:
	# 					shutil.copy2(full_path, new_file)
	# 				except:
	# 					pass

	# 				head, tail = ntpath.split(new_file)
	# 				os.chdir(head)

	# 				try:
	# 					tFile.add(tail)
	# 				except:
	# 					_logger.error("No se encontro el archivo: %s" %tail)
				
	# 			tFile.close()
	# 			os.chdir(original_dir)

	# 			values = {
	# 				'name': file_name + '.tar.gz',
	# 				'datas_fname': file_name + '.tar.gz',
	# 				'res_model': 'download.attachment',
	# 				'res_id': ids[0],
	# 				'res_name': 'test',
	# 				'type': 'binary',
	# 				'store_fname': 'attachments/attachments',
	# 				'active' : False,
	# 			}

	# 			attachment_id = self.env['ir.attachment'].create(values)
	# 			url = "%s/web/content/%s?download=true" % (value, attachment_id.id)

	# 			return {
	# 				'type': 'ir.actions.act_url',
	# 				'url': url,
	# 				'nodestroy': False,
	# 			}
