## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)

class wizard_viaje(models.TransientModel):
    #METODOS
    def _get_viaje_seleccionados(self):
        r=self.env["trafitec.viajes"].browse(self.env.context.get('active_ids'))
        self._total()
        return r

    def _get_viaje_sin_cr(self):
        r=self.env["trafitec.viajes"].search(['&',('active','=',True),('en_contrarecibo','=',False),('tipo_viaje','=','Normal')])
        self._total()
        return r

    
    def actualiza_viajes(self):
        for v in self.viajes_id:
            v.en_contrarecibo=True

    @api.constrains('viajes_id','asociado_id')
    def _valida(self):
        for v in self.viajes_id:
            if v.en_contrarecibo==True:
                raise ValidationError("El viaje con folio: %s ya tiene contra recibo." % v.name)

        if self.asociado_id!=self.factura_id.partner_id:
           raise ValidationError("El asociado de la carta porte es diferente al del contra recibo.")

    @api.onchange('asociado_id')
    def _cambio_asociado(self):
        self._carga_viajes()

    def _carga_viajes(self):
        self.viajes_id=[]
        self.viajes_id=self.env["trafitec.viajes"].search(['&',('asociado_id','=',self.asociado_id.id),('active','=',True)])


    
    @api.depends('viajes_id', 'total','subtotal','iva','riva')
    def _total(self):
        subtotal=0
        iva=0
        riva=0
        total=0
        for v in self.viajes_id:
            subtotal = subtotal + v.flete_asociado
            #totalc += 1

        iva=subtotal*0.16
        riva=subtotal*0.04
        total=subtotal+iva-riva

        self.subtotal=subtotal
        self.iva=iva
        self.riva=riva
        self.total=total

    #CAMPOS
    _name="wizard.viaje"
    nombre=fields.Char(string="Nombre:")
    apellidos=fields.Char(string="Apellidos:")
    asociado_id=fields.Many2one(comodel_name="res.partner",string="Asociado:", required=True)
    viajes_id=fields.Many2many("trafitec.viajes",string="Viajes:",default=_get_viaje_seleccionados)
    factura_id=fields.Many2one("account.invoice",string="Carta porte:",required=True,domain=[('type','=','out_invoice')])
    comisiones_id=fields.Many2many("trafitec.cargos",string="Comisiones:",required=True)

    subtotal=fields.Float(string="SubTotal:",compute='_total')
    iva=fields.Float(string="IVA:",compute='_total')
    riva=fields.Float(string="RIVA:",compute='_total')
    total=fields.Float(string="Total:",compute='_total')
