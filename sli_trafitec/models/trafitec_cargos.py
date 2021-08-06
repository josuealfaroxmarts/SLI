## -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
_logger = logging.getLogger(__name__)


class TrafitecCargos(models.Model):
    _name = "trafitec.cargos"    
    _order= "id desc"
    _description = "Cargos"

    viaje_id = fields.Many2one(
        "trafitec.viajes",
        string="Viajes ID",
        ondelete="cascade",
        readonly=False
    )
    monto = fields.Float(
        string="Monto",
        readonly=False
    )
    tipo_cargo = fields.Selection(
        string="Tipo de cargo",
        selection=[
            ("comision", "comision"),
            ("merma", "merma"),
            ("descuentos", "descuentos")]
    )
    asociado_id = fields.Many2one(
        "res.partner",
        domain="[('asociado', '=',True)]",
        string="Asociado",
        required=True,
        readonly=False
    )
    descuento_id = fields.Many2one(
        "trafitec.descuentos",
        string="ID descuentos",
        ondelete="cascade"
    )
    abono_id = fields.One2many(
        "trafitec.comisiones.abono",
        "abonos_id"
    )
    valor = fields.Char(string="valor")
    abonado = fields.Float(
        compute="_compute_abonado",
        string="Abonado",
        store=True
    )

    def unlink(self):
        if len(self)>1:
            raise UserError(_(
                "Alerta..\nNo se puede eliminar mas de una comisión a la vez."))
        if self.tipo_cargo == "comision":
            if self.viaje_id.id != False:
                raise UserError(_(
                    "Aviso !\nNo se puede eliminar una comision que tenga viajes."))
            if self.abonado > 0:
                raise UserError(_(
                    "Aviso !\nNo se puede eliminar una comision que tenga abonos."))
        return super(TrafitecCargos, self).unlink()

    def name_get(self):
        result = []
        name=""
        for rec in self:
            if rec.id:
                name = str(rec.id)+" "
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    @api.depends("abono_id.name")
    def _compute_abonado(self):
        self.abonado = sum(line.name for line in self.abono_id)


    
    @api.depends("abono_id","monto","abonado")
    def _compute_saldo(self):
        #if self.tipo_cargo == "comision":
        #    if self.abonado:
                self.saldo = self.monto - self.abonado
        #    else:
        #        self.saldo = self.monto

    saldo = fields.Float(compute="_compute_saldo",string="Saldo",store=True)




class trafitec_descuentos_abono(models.Model):
    _name = "trafitec.descuentos.abono"
    _description = "Descuentos y abonos"

    name = fields.Float(string="Abono", required=True)
    fecha = fields.Date(string="Fecha", required=True, default=fields.Datetime.now)
    observaciones = fields.Text(string="Observaciones")
    tipo = fields.Selection([("manual","Manual"),("contrarecibo","Contra recibo")],string="Tipo", default="manual")
    abonos_id = fields.Many2one("trafitec.descuentos", ondelete="cascade")
    contrarecibo_id = fields.Many2one("trafitec.contrarecibo", ondelete="restrict")
    permitir_borrar = fields.Boolean(string="Permitir borrar", default=False)

    
    def unlink(self):
        #if self.tipo == "contrarecibo":
        #    if self.permitir_borrar != False:
        #        raise UserError(_(
        #            "Aviso !\nNo se puede eleminar un abono de un contra recibo."))
        #if self.tipo == "manual":
        #obj = self.env["trafitec.con.descuentos"].search([("descuento_fk", "=", self.abonos_id.id), ("linea_id.state", "=", "Nueva")])
        #for des in obj:
        #    res = des.saldo + self.name
        #    abonado = des.anticipo - res
        #    des.write({"saldo": res, "abonos": abonado, "abono": res})
        return super(trafitec_descuentos_abono, self).unlink()

    @api.constrains("name")
    def _check_abono(self):
        if self.name <= 0:
            raise UserError(_("Aviso !\nEl monto del abono debe ser mayor a cero."))

    @api.constrains("name")
    def _check_monto_mayor(self):
        obj_abono = self.env["trafitec.descuentos.abono"].search([("abonos_id","=",self.abonos_id.id)])
        amount = 0
        for abono in obj_abono:
            amount += abono.name
        
        #if amount > self.abonos_id.monto:
        #   raise UserError(_("Aviso !\nEl monto de abonos ha sido superado al monto del descuento."))


    @api.model
    def create(self, vals):
        id =  super(trafitec_descuentos_abono, self).create(vals)
        if "tipo" in vals:
            tipo = vals["tipo"]
        else:
            tipo = "manual"
        valores = {
            "descuento_abono_id" : id.id,
            "monto": vals["name"],
            "detalle": vals["observaciones"],
            "cobradoen" : "Descuento {}".format(tipo)
        }
        self.env["trafitec.abonos"].create(valores)
        if tipo == "manual":
            obj = self.env["trafitec.con.descuentos"].search([("descuento_fk","=",vals["abonos_id"]),("linea_id.state","=","Nueva")])
            for des in obj:
                res = des.saldo - vals["name"]
                abonado = des.anticipo - res
                des.write({"saldo":res, "abonos": abonado, "abono":res})
        return id

    
    def write(self, vals):
        if "name" in vals:
            monto = vals["name"]
        else:
            monto = self.name
        if "observaciones" in vals:
            detalle = vals["observaciones"]
        else:
            detalle = self.observaciones
        valores = {
            "monto": monto,
            "detalle": detalle
        }
        obj = self.env["trafitec.abonos"].search([("descuento_abono_id","=",self.id)])
        obj.write(valores)
        if self.tipo == "manual" and "name" in vals:
            obj = self.env["trafitec.con.descuentos"].search([("descuento_fk","=",self.abonos_id.id),("linea_id.state","=","Nueva")])
            for des in obj:
                if self.name > vals["name"]:
                    res = des.saldo + (self.name - vals["name"])
                else:
                    res = des.saldo - (vals["name"] - self.name)
                if res == 0:
                    des.unlink()
                else:
                    abonado = des.anticipo - res
                    des.write({"saldo":res, "abonos": abonado, "abono":res})

        return super(trafitec_descuentos_abono, self).write(vals)

class trafitec_comisiones_abono(models.Model):
    _name = "trafitec.comisiones.abono"
    _description="comisiones abono"
    name = fields.Float(string="Abono", required=True)
    fecha = fields.Date(string="Fecha", required=True, default=fields.Datetime.now)
    observaciones = fields.Text(string="Observaciones")
    tipo = fields.Selection([("manual","Manual"),("contrarecibo","Contra recibo")],string="Tipo", default="manual")
    abonos_id = fields.Many2one("trafitec.cargos", ondelete="cascade")
    contrarecibo_id = fields.Many2one("trafitec.contrarecibo", ondelete="restrict")
    permitir_borrar = fields.Boolean(string="Permitir borrar", default=False)

    
    def unlink(self):
        #if self.tipo == "contrarecibo":
            #if self.permitir_borrar != False:
            #    raise UserError(_(
            #        "Aviso !\nNo se puede eleminar un abono de un contra recibo."))

        if self.tipo == "manual":
            obj = self.env["trafitec.con.comision"].search(
                [("cargo_id", "=", self.abonos_id.id), ("line_id.state", "=", "Nueva")])
            for con in obj:
                res = con.saldo + self.name
                abonado = con.comision - res
                con.write({"saldo": res, "abonos": abonado})
        return super(trafitec_comisiones_abono, self).unlink()

    @api.constrains("name")
    def _check_abono(self):
        if self.name <= 0:
            raise UserError(_(
                "Aviso !\nEl monto del abono debe ser mayor a cero."))

    @api.constrains("name")
    def _check_monto_mayor(self):
        obj_abono = self.env["trafitec.comisiones.abono"].search([("abonos_id","=",self.abonos_id.id)])
        amount = 0
        for abono in obj_abono:
            amount += abono.name
        if amount > self.abonos_id.monto:
            raise UserError(_(
                "Aviso !\nEl monto de abonos ha sido superado al monto de la comision."))


    @api.model
    def create(self, vals):
        id =  super(trafitec_comisiones_abono, self).create(vals)
        if "tipo" in vals:
            tipo = vals["tipo"]
        else:
            tipo = "manual"
        valores = {
            "comision_abono_id" : id.id,
            "monto": vals["name"],
            "detalle": vals["observaciones"],
            "cobradoen" : "Comision {}".format(tipo)
        }
        self.env["trafitec.abonos"].create(valores)
        if tipo == "manual":
            obj = self.env["trafitec.con.comision"].search([("cargo_id","=",vals["abonos_id"]),("line_id.state","=","Nueva")])
            for con in obj:
                res = con.saldo - vals["name"]
                abonado = con.comision - res
                con.write({"saldo":res, "abonos": abonado})
        return id

    
    def write(self, vals):
        if "name" in vals:
            monto = vals["name"]
        else:
            monto = self.name
        if "observaciones" in vals:
            detalle = vals["observaciones"]
        else:
            detalle = self.observaciones
        valores = {
            "monto": monto,
            "detalle": detalle
        }
        obj = self.env["trafitec.abonos"].search([("comision_abono_id","=",self.id)])
        obj.write(valores)

        if self.tipo == "manual" and "name" in vals:
            obj = self.env["trafitec.con.comision"].search([("cargo_id","=",self.abonos_id.id),("line_id.state","=","Nueva")])
            for con in obj:
                if self.name > vals["name"]:
                    res = con.saldo + (self.name - vals["name"])
                else:
                    res = con.saldo - (vals["name"] - self.name)
                abonado = con.comision - res
                con.write({"saldo": res, "abonos": abonado})


        return super(trafitec_comisiones_abono, self).write(vals)