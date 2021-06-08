# -*- coding: utf-8 -*-

from requests.models import DecodeError
from odoo import models, fields, api
import base64
import requests
import logging
import imghdr
import json
_logger = logging.getLogger(__name__)

class SyncDataFletex(models.Model):
    _name = 'sync.data.fletex'

    address = fields.Text(string='')

    def sync_data(self) :
        """Start data sync with fletex"""

        token = self.login_to_fletex() #Login to fletex to get token API
        
        #A header is created with the authentication token
        headers = {
            'Authorization': token
        }
        
        #FLETEX is requested all users in pending status 
        users = self.response_fletex(
            self.get_endpoint('read_users_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers' : headers,
                'params': {}
            })
        
        if len(users) > 0 :
            for user in users['data'] :
                self.res_partner_manager(user,headers)
        else :
            _logger.debug('No users as pending')
        
    def login_to_fletex(self) :
        """Login to Fletex to get token"""
        response = self.response_fletex(
            self.get_endpoint('auth_login_fletex_endpoint'),
            'post',
            {
                'data': {},
                'headers' : {},
                'params': {
                    'pinDriver': self.get_endpoint('username'),
                    'password': self.get_endpoint('password')
                }
            })
        
        return "{} {}".format(response['token_type'].capitalize(),response['access_token'])

    def response_fletex(self, endpoint, method, data={}) :
        url = self.env["ir.config_parameter"].sudo().get_param(
            'api_fletex_url'
        )
        
        if method == "post" :
            response = requests.post(
                "{}{}".format(url,endpoint),
                data=json.dumps(data['data']),
                headers=data['headers'],
                params=data['params'])
        elif method == "get"  :
            response = requests.get(
                "{}{}".format(url,endpoint),
                data=data['data'],
                headers=data['headers'],
                params=data['params'])

        if response.status_code == 200:
            return response.json()
        else :
            _logger.debug(response.text)
            return response

    def get_endpoint(self, endpoint_id) :
        return self.env["ir.config_parameter"].sudo().get_param(
            endpoint_id)

    def verify_status (self, user_id) :
        pass

    def res_partner_manager(self, user, headers) :

        record = self.env['res.partner'].search([
            ('email','=',user['account_email'])])
            
        if len(record) > 0 :
            if record['status_client'] == 'Aprobado' :
                status = "active" 
            elif record['status_client'] == 'Rechazado' :
                status = "rejected"
            else :
                status = "pending"
            response = self.response_fletex(
                self.get_endpoint('read_users_fletex_endpoint'),
                'post',
                {
                    'data': {
                                'users': [
                                    {
                                        'user_id': 524,
                                        'status': status,
                                    }
                                ]
                        },
                    'headers' : headers,
                    'params': {}
                })
            _logger.debug(status)
            _logger.debug(status)
            _logger.debug(user['user_id'])
        else :
            vals = {
                'asociado': (True
                                if user['role'] == "carrier"
                                else False),
                'operador': (True
                                if user['role'] == "driver"
                                else False),
                'supplier': (True
                                if user['role'] == "carrier"
                                else False),
                'customer': (True
                                if user['role'] == "client"
                                else False),
                'image': user['profile_pic'],
                'name': "{} {}".format(user['account_name'],user['account_last_name'])
                        if user['account_type'] != "moral"
                        else "{}".format(user['social_reason']),
                'razon_social': "{} {}".format(user['account_name'],user['account_last_name'])
                        if user['account_type'] == "moral"
                        else "{}".format(user['social_reason']),
                'company_type2': ("person"
                                if user['account_type'] != "moral"
                                else "company"),
                'vat': user['rfc_empresa'],
                'rfc_moral': user['rfc'],
                'street': user['street'],
                'l10n_mx_street3': user['ext_num'],
                'l10n_mx_street4': user['int_num'],
                'zip_sat_id': self.search_zip(user['zip']),
                'colonia_sat_id': self.search_colonia(user['neighborhood']),
                'township_sat_id': self.search_township(user['city']),
                'state_id': self.search_state(user['state']),
                'email': user['account_email'],
                'nombre_moral': user['legal_representative']['name'],
                'apellido_moral': user['legal_representative']['lastName'],
                'correo_moral': user['legal_representative']['email'],
                'rfc_fisica': user['rfc'],
                'identificacion_representante_moral': None 
                            if not 'ine_drop' in user['documents']
                            else user['documents']['ine_drop'],
                'ext_identificacion_representante_moral':None 
                            if not 'ine_drop' in user['documents']
                            else self.find_extension_document(
                    user['documents']['ine_drop']),
                'acta_moral': None 
                            if not 'ine_drop' in user['documents']
                            else user['documents']['ine_drop'],
                'ext_acta_moral': None 
                            if not 'ine_drop' in user['documents']
                            else self.find_extension_document(
                    user['documents']['ine_drop']),
                'domicilio_moral': None 
                            if not 'ine_drop' in user['documents']
                            else user['documents']['ine_drop'],
                'ext_domicilio_moral': None 
                            if not 'ine_drop' in user['documents']
                            else self.find_extension_document(
                    user['documents']['ine_drop']),
                'identificacion_representante_fisica': None 
                            if not 'ine_drop' in user['documents']
                            else user['documents']['ine_drop'],
                'ext_iden_fisica':None 
                            if not 'ine_drop' in user['documents']
                            else self.find_extension_document(
                    user['documents']['ine_drop']),
                'comprobante_domicilio_fisica': None 
                            if not 'ine_drop' in user['documents']
                            else user['documents']['ine_drop'],
                'ext_comprobante_domicilio_fisica': None 
                            if not 'ine_drop' in user['documents']
                            else self.find_extension_document(
                    user['documents']['ine_drop']),
                'status_client': 'Borrador',
                'progress_fletex': 100.0,
                'step_one': True,
                'step_two': True,
                'step_three': True,
                
                
            }
            record = self.env['res.partner'].create(vals)

    def search_zip(self,zip_code) :
        record = self.env['res.country.zip.sat.code'].search([
            ('code','=',zip_code)])
        if len(record) > 0 :
            return record['id']
        else :
            return None

    def search_colonia(self,colonia) :
        record = self.env['res.colonia.zip.sat.code'].search([
            ('name','=',colonia)])
        if len(record) > 0 :
            return record['id']
        else :
            return None

    def search_township(self,township) :
        record = self.env['res.country.township.sat.code'].search([
            ('name','=',township)])
        if len(record) > 0 :
            return record['id']
        else :
            return None

    def search_state(self,state) :
        record = self.env['res.country.state'].search([
            ('name','=',state)])
        if len(record) > 0 :
            return record['id']
        else :
            return None

    def find_extension_document(self, document) :
        document = base64.b64decode(document)
        return imghdr.what(None, h=document)