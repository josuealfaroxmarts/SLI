# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo import models, fields, api, _, tools


class SalespersonWizard(models.TransientModel):
	_name = "salesperson.wizard"
	_description = "Salesperson Wizard"

	def check_report(self):
		data = {}
		data["form"] = self.read(
			["salesperson_id", "date_from", "date_to"]
		)[0]

		return self._print_report(data)

	def _print_report(self, data):
		data["form"].update(self.read(
			["salesperson_id", "date_from", "date_to"]
		)[0])

		return self.env["report"].get_action(
			self,
			"sales_report.report_salesperson",
			data=data
		)

	@api.model
	def render_html(self, docids, data=None):
		self.model = self.env.context.get("active_model")
		docs = self.env[self.model].browse(self.env.context.get("active_id"))
		sales_records = []
		orders = self.env["sale.order"].search([
			("user_id", "=", docs.salesperson_id.id)
		])

		if docs.date_from and docs.date_to:
			for order in orders:
				if ( 
					int(docs.date_from) <= int(order.date_order)
					and int(docs.date_to) >= int(order.date_order)
				):
					sales_records.append(order)
				else:
					raise UserError("Please enter duration")

		docargs = {
			"doc_ids": self.ids,
			"doc_model": self.model,
			"docs": docs,
			"time": time,
			"orders": sales_records}

		return self.env["report"].render(
			"sales_report.report_salesperson",
			docargs
		)