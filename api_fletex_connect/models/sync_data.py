# -*- coding: utf-8 -*-
from os import stat
from requests.models import DecodeError
from odoo import models, fields, api
import base64
import requests
import logging
import imghdr
import sys
_logger = logging.getLogger(__name__)


class SyncDataFletex(models.Model):
    _name = 'sync.data.fletex'

    def sync_data(self):
        """In this function, requests are made to FLETEX and calls 
        are made to the other functions for saving or modifying the registry."""

        # Variable where headers are stored
        headers = {
            'Authorization': self.env["ir.config_parameter"].sudo().get_param(
                'token_api_fletex'),
        }

        # Users are requested to FLETEX
        users = self.response_fletex(
            self.get_endpoint('read_users_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers': headers,
                'params': {}
            })

        # If the request brings users, the user manager is called
        if users :
            if len(users['data']) > 0:
                for user in users['data']:
                    if user['role'] == 'driver':
                        self.res_partner_drivers_manager(user)
                    else:
                        self.res_partner_manager(user)
        self.update_res_partners(headers)

        # Vehicles are requested to FLETEX
        vehicles = self.response_fletex(
            self.get_endpoint('read_vehicles_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers': headers,
                'params': {}
            })

        if vehicles :
            if len(vehicles) > 0:
                for vehicle in vehicles['data']:
                    self.vehicles_manager(vehicle)

        self.change_status_vehicle(headers)

        # Locations are requested to FLETEX
        locations = self.response_fletex(
            self.get_endpoint('read_locations_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers': headers,
                'params': {}
            })

        # If the request brings locations, the locations manager is called
        if locations: 
            if len(locations) > 0:
                for location in locations['data']:
                    self.locations_manager(location, headers)

        responsables = self.response_fletex(
                self.get_endpoint('read_responsibles_fletex_endpoint'),
                'get',
                {
                    'data': {},
                    'headers': headers,
                    'params': {}
                })

        if responsables :
            if len(responsables['data']) > 0:
                for responsable in responsables['data']:
                    self.responsables_manager(responsable)

        # projects are requested to FLETEX
        projects = self.response_fletex(
            self.get_endpoint('read_projects_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers': headers,
                'params': {}
            })
        # If the request brings locations, the locations manager is called
        
        if projects :
            if len(projects['data']) > 0:
                for project in projects['data']:
                    self.projects_manager(project, headers)

        self.change_status_projects(headers)

        shipments = self.response_fletex(
            self.get_endpoint('read_shipments_fletex_endpoint'),
            'get',
            {
                'data': {},
                'headers': headers,
                'params': {}
            })
        _logger.info('@@@@@@@@@@@@@s@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
        _logger.info(projects)
        # If the request brings locations, the locations manager is called
        if shipments : 
            if len(shipments['data']['shipments']) > 0:
                for shipment in shipments['data']['shipments']:
                    self.shipments_manager(shipment)

    def response_fletex(self, endpoint, method, data={}):
        """ This function makes the call to the different endpoints 
        of the fletex API and returns the information hosted by the platform
        parameters :
        endponit (string) = endpoint where the request will be made
        method (string) = http method used for the request
        data (dict) = data that will be sent to the endpoint, must contain, data, 
        headers and params
        """

        url = self.env["ir.config_parameter"].sudo().get_param(
            'api_fletex_url'
        )

        if method == "post":
            data['headers']['Content-type'] = 'application/json'
            response = requests.post(
                "{}{}".format(url, endpoint),
                json=data['data'],
                headers=data['headers'],
                params=data['params'])
        elif method == "get":
            response = requests.get(
                "{}{}".format(url, endpoint),
                data=data['data'],
                headers=data['headers'],
                params=data['params'])

        try :
            if response.status_code == 200:
                return response.json()
            else:
                _logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@RESPOSNE@@@@@@@@@@@@@@@@@@@@@@")
                _logger.info(response)
                return False
        except : 
            return [];


    def get_endpoint(self, endpoint):
        """Get and return the end point saved in odoo configuration"""
        return self.env["ir.config_parameter"].sudo().get_param(
            endpoint)

    def res_partner_manager(self, user):
        res_partner = self.env['res.partner'].search(
            [('id_fletex', '=', user['user_id'])])
        vals = {
            'id_fletex': user['user_id'],
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
            'phone_representative': user['legal_representative']['phone'],
            'image_1920': user['profile_pic'],
            'name': "{} {}".format(user['account_name'], user['account_last_name'])
            if user['account_type'] != "moral"
            else "{}".format(user['social_reason']),
            'legal_representative': "{} {}".format(user['account_name'], user['account_last_name'])
            if user['account_type'] == "moral"
            else "{}".format(user['social_reason']),
            'company_type': ("person"
                                if user['account_type'] != "moral"
                                else "company"),
            'asociado_operador':  self.env['res.partner'].search([('id_fletex', '=', user['carrier_id'])])
            if user['role'] == "driver"
            else False,
            'vat': user['rfc_empresa'],
            'rfc_representative': user['rfc'],
            'street': user['street'],
            'street_number': user['ext_num'],
            'street_number2': user['int_num'],
            'zip': user['zip'],
            'city': user['city'],
            'state_id': self.search_record('res.country.state',
                                            'name',
                                            user['state']),
            'email': user['account_email'],
            'name_representative': user['legal_representative']['name'],
            'lastname_representative': user['legal_representative']['lastName'],
            'email_representative': user['legal_representative']['email'],
            'phone_representative': user['legal_representative']['phone'],
            'rfc_representative': user['rfc'],
            'id_representative': None
            if not 'ine_drop' in user['documents']
            else user['documents']['ine_drop'],
            'ext_id_representative': None
            if not 'ine_drop' in user['documents']
            else self.find_extension_document(
                user['documents']['ine_drop']),
            'act_representative': None
            if not 'constitutive_act_drop' in user['documents']
            else user['documents']['constitutive_act_drop'],
            'ext_act_representative': None
            if not 'constitutive_act_drop' in user['documents']
            else self.find_extension_document(
                user['documents']['constitutive_act_drop']),
            'address_representative': None
            if not 'proof_of_tax_address_drop' in user['documents']
            else user['documents']['proof_of_tax_address_drop'],
            'ext_address_representative': None
            if not 'proof_of_tax_address_drop' in user['documents']
            else self.find_extension_document(
                user['documents']['proof_of_tax_address_drop']),
            'rfc_representative_drop': None
            if not 'rfc_drop' in user['documents']
            else user['documents']['rfc_drop'],
            'ext_representative_drop': None
            if not 'rfc_drop' in user['documents']
            else self.find_extension_document(
                user['documents']['rfc_drop']),
            'rfc_bussiness': None
            if not 'rfc_empresa_drop' in user['documents']
            else user['documents']['rfc_empresa_drop'],
            'ext_rfc_bussiness': None
            if not 'rfc_empresa_drop' in user['documents']
            else self.find_extension_document(
                user['documents']['rfc_empresa_drop']),
            'status_record': 'draft',
            'status_fletex': 'completed',
            'progress_fletex': 100.0,
            'step_one': True,
            'step_two': True,
            'step_three': True,
        }

        """User is created if there is no match in Odoo"""
        if len(res_partner) > 0:
            if not res_partner['send_to_api']:
                res_partner.write(vals)
                self.save_result_sync(
                    "Usuario modificado",
                    "Correo: {}".format(user['account_email'],),
                    "Exitoso"
                )
        else:
            self.env['res.partner'].create(vals)
            self.save_result_sync(
                "Nuevo usuario creado",
                "Correo: {}".format(user['account_email'],),
                "Exitoso"
            )

    def res_partner_drivers_manager(self, user):
        drivers = self.env['res.partner'].search([
            ('driver_id_fletex', '=', user['user_id'])
        ])

        carrier_id = self.env['res.partner'].search([
            ('id_fletex', '=', user['carrier_id'])
        ])
        vals = {
            'driver_id_fletex': user['user_id'],
            'operador': True,
            'image_1920': user['profile_pic'],
            'name': "{} {}".format(user['name'], user['last_name']),
            'asociado_operador': carrier_id['id'],
            'mobile': user['phone'],
            'license_driver': None
            if not 'file_licence' in user['documents']
            else user['documents']['file_licence'],
            'ext_license_driver': None
            if not 'file_licence' in user['documents']
            else self.find_extension_document(
                    user['documents']['file_licence']),
            'email': "{}@sli.mx".format(user['healthcare_number']),
            'status_record': 'draft',
            'status_fletex': 'completed',
            'progress_fletex': 100.0,
            'healthcare_number': user['healthcare_number'],
            'adj_healthcare_number': None
            if not 'file_nss' in user['documents']
            else user['documents']['file_nss'],
            'ext_healthcare_number': None
            if not 'file_nss' in user['documents']
            else self.find_extension_document(
                user['documents']['file_nss']),
        }

        """User is created if there is match in Odoo"""
        if len(drivers) > 0:
            if not drivers['send_to_api']:
                drivers.write(vals)
                self.save_result_sync(
                    "Operador modificado",
                    "Seguro Social: {}".format(user['healthcare_number'],),
                    "Exitoso"
                )
        else:
            self.env['res.partner'].create(vals)
            self.save_result_sync(
                "Nuevo operador creado",
                "Seguro Social: {}".format(user['healthcare_number'],),
                "Exitoso"
            )

    def update_res_partners(self, headers):
        rejected_files = []
        """
            If the status in odoo is rejected, 
            it is verified which document was rejected.
            If approved, the status and credit limit are updated
            """
        res_partners = self.env['res.partner'].search(
            [('send_to_api', '=', True)])
        _logger.info('RESPARTNESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
        for res_partner in res_partners:
            if res_partner['operador']:
                rejected_files = []
                if res_partner['status_record'] == 'refused':
                    new_driver = 1
                    status = 'rejected'
                    if not res_partner['nss_approved']:
                        rejected_files.append('file_nss')
                    if not res_partner['license_approved']:
                        rejected_files.append('file_license')
                elif res_partner['status_record'] == 'draft':
                    continue
                else:
                    status = 'active'
                    new_driver = None
                _logger.info(rejected_files)
                response = self.response_fletex(
                    self.get_endpoint('read_users_fletex_endpoint'),
                    'post',
                    {
                        'data': {
                            'users': [
                                {
                                    'user_id': res_partner['driver_id_fletex'],
                                    'status': status,
                                    'rejected_files': rejected_files
                                }
                            ]
                        },
                        'headers': headers,
                        'params': {}
                    })
                _logger.info(response)
                

            else:
                if res_partner['status_record'] == 'refused':
                    status = "rejected"
                    if not res_partner['id_approved']:
                        rejected_files.append('ine_drop')
                    if not res_partner['act_approved']:
                        rejected_files.append('constitutive_act_drop')
                    if not res_partner['address_approved']:
                        rejected_files.append('proof_of_tax_address_drop')
                    if not res_partner['rfc_approved']:
                        rejected_files.append('rfc_empresa_drop')
                    if not res_partner['rfc_representative_drop_approved']:
                        rejected_files.append('rfc_drop')
                elif res_partner['status_record'] == 'draft':
                    continue
                else:
                    status = "active"

                credit_limit = res_partner['limit_credit']

                """We send all the data to fletex for updating"""
                response = self.response_fletex(
                    self.get_endpoint('read_users_fletex_endpoint'),
                    'post',
                    {
                        'data': {
                            'users': [
                                {
                                    'user_id': res_partner['id_fletex'],
                                    'credit_limit': credit_limit,
                                    'status': status,
                                    "rejected_files": rejected_files
                                }
                            ]
                        },
                        'headers': headers,
                        'params': {}
                    })

            res_partner.write({'send_to_api': False})

    def vehicles_manager(self, vehicle):
        """ This function is in charge of managing the vehicles that are sent from fletex :
            vehicle (dict) = dictionary with vehicle data
            headers (dict) = headers used for the request
        """

        """a match of the user is searched in Odoo, 
        if it does not exist, it is created"""
        if vehicle['type'] == 'truck':
            record = self.env['fleet.vehicle'].search([
                ('id_fletex_truck', '=', vehicle['vehicle_id'])])
        else:
            record = self.env['fleet.vehicle'].search([
                ('id_fletex_trailer', '=', vehicle['vehicle_id'])])

        if len(record) > 0:

            brand_id = self.env['fleet.vehicle.model.brand'].create(
                {'name': vehicle['brand']})
            model_id = self.env['fleet.vehicle.model'].create({
                'name': vehicle['year'],
                'brand_id': brand_id.id
            })

            """ The ID is searched in Odoo of the 
            user to whom this vehicle belongs """
            asociado_id = self.search_record(
                'res.partner',
                'id_fletex',
                vehicle['business_id'])

            vals = {
                'id_fletex_truck': vehicle['vehicle_id']
                if vehicle['type'] == 'truck'
                else None,
                'id_fletex_trailer': vehicle['vehicle_id']
                if vehicle['type'] == 'trailer'
                else None,
                'image_128': vehicle['vehicle_picture'],
                'model_id': model_id.id,
                'license_plate': vehicle['license_plate'],
                'numero_economico': vehicle['economic'],
                'tipo_vehiculo': 'tractocamion'
                if vehicle['type'] == 'truck'
                else 'remolque',
                'circulacion': None
                if not 'file_circulation_card' in vehicle['documents']
                else vehicle['documents']['file_circulation_card'],
                'ext_circulacion': None
                if not 'file_circulation_card' in vehicle['documents']
                else self.find_extension_document(
                    vehicle['documents']['file_circulation_card']),
                'poliza_seguro': None
                if not 'file_insurance_policy' in vehicle['documents']
                else vehicle['documents']['file_insurance_policy'],
                'ext_poliza_seguro': None
                if not 'file_insurance_policy' in vehicle['documents']
                else self.find_extension_document(
                    vehicle['documents']['file_insurance_policy']),
                'color_vehicle': vehicle['model'],
                'asociado_id': asociado_id,
                'es_flotilla': False
            }

            """New vehicle is registered in Odoo"""
            record.write(vals)

            self.save_result_sync(
                "Modificacion de vehículo",
                "Modelo: {}/{}, placa: {}".format(vehicle['year'],
                                                vehicle['brand'],
                                                vehicle['license_plate']),
                "Exitoso"
            )

        else:
            """
            Due to the inconsistency of data between Fletex and Odoo, 
            it is verified if the model and brand of the vehicle exists in odoo, 
            if not, it will be created.
            Note: By request of SLI, the model will not be used, 
            it will be replaced by the year of the vehicle
            """
            brand_id = self.env['fleet.vehicle.model.brand'].create(
                {'name': vehicle['brand']})
            model_id = self.env['fleet.vehicle.model'].create({
                'name': vehicle['year'],
                'brand_id': brand_id.id
            })

            """ The ID is searched in Odoo of the 
            user to whom this vehicle belongs """
            asociado_id = self.search_record(
                'res.partner',
                'id_fletex',
                vehicle['business_id'])

            vals = {
                'id_fletex_truck': vehicle['vehicle_id']
                if vehicle['type'] == 'truck'
                else None,
                'id_fletex_trailer': vehicle['vehicle_id']
                if vehicle['type'] == 'trailer'
                else None,
                'image_128': vehicle['vehicle_picture'],
                'model_id': model_id.id,
                'license_plate': vehicle['license_plate'],
                'numero_economico': vehicle['economic'],
                'tipo_vehiculo': 'tractocamion'
                if vehicle['type'] == 'truck'
                else 'remolque',
                'circulacion': None
                if not 'file_circulation_card' in vehicle['documents']
                else vehicle['documents']['file_circulation_card'],
                'ext_circulacion': None
                if not 'file_circulation_card' in vehicle['documents']
                else self.find_extension_document(
                    vehicle['documents']['file_circulation_card']),
                'poliza_seguro': None
                if not 'file_insurance_policy' in vehicle['documents']
                else vehicle['documents']['file_insurance_policy'],
                'ext_poliza_seguro': None
                if not 'file_insurance_policy' in vehicle['documents']
                else self.find_extension_document(
                    vehicle['documents']['file_insurance_policy']),
                'color_vehicle': vehicle['model'],
                'asociado_id': asociado_id,
                'ejes_tracktocamion': vehicle['tipe_ejes'],
                'es_flotilla': False
            }

            """New vehicle is registered in Odoo"""
            record = self.env['fleet.vehicle'].create(vals)

            self.save_result_sync(
                "Registro de vehículo nuevo",
                "Modelo: {}/{}, placa: {}".format(vehicle['year'],
                                                vehicle['brand'],
                                                vehicle['license_plate']),
                "Exitoso"
            )

    def change_status_vehicle(self, headers):

        vehicles_change = self.env['fleet.vehicle'].search(
            [('send_to_api', '=', True)])

        if len(vehicles_change) > 0:
            for vehicle in vehicles_change:
                
                rejected_files = []
                if vehicle['status_vehicle'] == 'rejected':
                    status = 'rejected'
                    if not vehicle['circulacion_approved']:
                        rejected_files.append('file_circulation_card,')
                    if not vehicle['poliza_approved']:
                        rejected_files.append('file_insurance_policy')
                elif vehicle['status_vehicle'] == 'approved':
                    status = 'active'
                else:
                    continue
                
                self.response_fletex(
                    self.get_endpoint('read_vehicles_fletex_endpoint'),
                    'post',
                    {
                        'data': {
                            'vehicles': [
                                {
                                    'vehicle_id': vehicle['id_fletex_trailer'] 
                                    if vehicle['tipo_vehiculo'] == 'remolque'
                                    else vehicle['id_fletex_truck'],
                                    'type': 'trailer'
                                    if vehicle['tipo_vehiculo'] == 'remolque'
                                    else 'truck',
                                    'status': status,
                                    'create_new_trailer': status
                                    if vehicle['tipo_vehiculo'] == 'remolque'
                                    else None,
                                    'create_new_truck': status
                                    if vehicle['tipo_vehiculo'] == 'tractocamion'
                                    else None,
                                    "rejected_files": rejected_files
                                }
                            ]
                        },
                        'headers': headers,
                        'params': {}
                    })
                
                vehicle.write({'send_to_api': False})


    def projects_manager(self, project, headers):
        """ This function is in charge of managing the projects that are sent 
        from fletex :
        project (dict) = dictionary with projects data
        headers (dict) = headers used for the request
        """

        records = self.env['trafitec.cotizacion'].search([
            ('id_fletex', '=', project['project_id']),
            ('send_to_api', '=', False)
        ])

        if len(records) > 0:
            for record in records:
                if record['status'] == 'approved':
                    status = 'Disponible'
                else:
                    status = 'Cancelada'

                vals = {
                    'status': status
                }


                record.write(vals)
        else:
            
            client_id = self.env['res.partner'].search(
                [('id_fletex',
                    '=',
                    project['user_id'])])
            elements = project['description'].replace(" ", "").split(',')

            product_id = self.env['product.product'].search(
                [('name',
                    '=', project['product'])])

            vals = {
                'id_fletex': project['project_id'],
                'nombre': project['name'],
                'lavada': True
                if 'Lavada' in elements
                else False,
                'fumigada': True
                if 'Fumigada' in elements
                else False,
                'limpia': True
                if 'Limpia' in elements
                else False,
                'otro': True
                if 'Otro' in elements
                else False,
                'chaleco': "Si"
                if 'Chaleco' in elements
                else "No",
                'calzado': "Si"
                if 'Calzado' in elements
                else "No",
                'lentes_seguridad': True
                if 'Lentes' in elements
                else False,
                'casco': True
                if 'Casco' in elements
                else False,
                'cubre_bocas': True
                if 'CubreBocas' in elements
                else False,
                'sua': "Si"
                if 'CubreBocas' in elements
                else "No",
                'costo_producto': project['assurance'],
                'seguro_mercancia': True
                if project['insurance'] == 1
                else False,
                'cliente': client_id['id'],
                'contacto2': client_id['id'],
                'codigo_postal': client_id['zip'],
                'ciudad': client_id['city'],
                'email': client_id['email'],
                'presentacion_carga': 'Granel'
                if project['product_presentation'] == "Toneladas"
                else 'Costal',
                'product': product_id['id'],
                'lineanegocio': self.search_record('trafitec.lineanegocio',
                                            'name',
                                            project['product_presentation']),
                'origen_id': self.search_record('trafitec.ubicacion',
                                                'id_fletex',
                                                project['location_id']),
                'destino_id': self.search_record('trafitec.ubicacion',
                                                'id_fletex',
                                                project['destinations'][0]),
                'currency_id': self.search_record('res.currency',
                                            'name','MXN')
            }

            quotation = self.env['trafitec.cotizacion'].create(vals)
            origin = self.search_record('trafitec.ubicacion',
                                        'id_fletex',
                                        project['location_id'])

            destination = self.search_record('trafitec.ubicacion',
                                        'id_fletex',
                                        project['destinations'][0])

            vals = {
                'municipio_origen_id': origin,
                'municipio_destino_id': destination,
                'tarifa_cliente': project['initial_fare'],
                'cantidad': project['total_weight'],
                'product_uom': self.search_record('uom.uom',
                                                'name', 'Tonelada'),
                'cotizacion_id': quotation.id,
                'distancia': 0.00,
                'tarifa_asociado': 1,
            }

            self.env['trafitec.cotizaciones.linea'].create(vals)

            for trailer in project['trailers']:
                vals = {
                    'tipo_camion': quotation.id,
                    'type_truck': trailer,
                }
                self.env['trafitec.type_truck'].create(vals)

    def change_status_projects(self, headers):
        projects = self.env['trafitec.cotizacion']\
            .search([('state', '=', 'Disponible'),
                    ('send_to_api', '=', True)])

        if len(projects) > 0:
            for project in projects:
                project_line = self.env['trafitec.cotizaciones.linea'].search(
                    [('cotizacion_id', '=', project['id'])])

                self.response_fletex(
                    self.get_endpoint('read_projects_fletex_endpoint'),
                    'post',
                    {
                        'data': {
                            'quotes': [
                                {
                                    'project_id': project['id_fletex'],
                                    'carrier_fare': project_line['tarifa_asociado'],
                                    'estimated_shipments': project_line['total_movimientos']
                                }
                            ]
                        },
                        'headers': headers,
                        'params': {}
                    })
                project.write({'send_to_api': False})

    def locations_manager(self, location, headers):
        """ This function is in charge of managing the locations that are 
        sent from fletex :
        location (dict) = dictionary with location data.
        headers (dict) = headers used for the request.
        """

        """a match of the location is searched in Odoo, 
        if it does not exist, it is created"""
        record = self.env['trafitec.ubicacion'].search([
            ('id_fletex', '=', location['location_id'])])
        _logger.debug(location['alias'])
        _logger.debug('Hello Bodegas!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1')
        if len(record) > 0:
            client_id = self.env['res.partner'].search([
                ('id_fletex', '=', location['user_id'])])
            _logger.debug('MODIFICANDOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO1111111111111')
            vals = {
                'id_fletex': location['location_id'],
                'name': location['alias'],
                'calle': location['street'],
                'estado': location['state'],
                'noexterior': location['ext_number'],
                'nointerior': location['int_number'],
                'ciudad': location['city'],
                'estado': location['state'],
                'colonia': location['neighborhood'],
                'codigo_postal': location['cp'],
                'comentarios': location['instructions'],
                'longitud': location['lng'],
                'latitud': location['lat'],
                'cliente_ubicacion': client_id['id'],
            }
            record.write(vals)
            self.save_result_sync(
                "Modificacion de bodega/puerto",
                "Nombre: {}".format(location['alias']),
                "Exitoso")
        else:
            
            client_id = self.env['res.partner'].search([
                ('id_fletex', '=', location['user_id'])])
                

            vals = {
                'id_fletex': location['location_id'],
                'name': location['alias'],
                'calle': location['street'],
                'estado': location['state'],
                'noexterior': location['ext_number'],
                'nointerior': location['int_number'],
                'ciudad': location['city'],
                'estado': location['state'],
                'colonia': location['neighborhood'],
                'codigo_postal': location['cp'],
                'comentarios': location['instructions'],
                'longitud': location['lng'],
                'latitud': location['lat'],
                'cliente_ubicacion': client_id['id'],
            }
            
            self.env['trafitec.ubicacion'].create(vals)
            """New location is registered in Odoo.
            As the locations have a record of their managers, 
            the managers are created by relating them to the location id
            """

            self.save_result_sync(
                "Registro de bodeaga/puerto nuevo",
                "Nombre: {}".format(location['alias']),
                "Exitoso")

    def responsables_manager (self, responsable) :
        location = self.env['trafitec.ubicacion'].search([
            ('id_fletex', '=', responsable['location_id'])])

        responsable_odoo = self.env['trafitec.responsable'].search([
            ('id_fletex', '=', responsable['responsible_id'])])

        if len(responsable_odoo) > 0 :
            vals = {
                'id_fletex': responsable['responsible_id'],
                'responsable': location['id'],
                'nombre_responsable': responsable['name'],
                'email_responsable':  responsable['email'],
                'telefono_responsable': responsable['phone_number']
            }

            responsable_odoo.write(vals)
        else :
            if len(location) > 0:
                vals = {
                    'id_fletex': responsable['responsible_id'],
                    'responsable': location['id'],
                    'nombre_responsable': responsable['name'],
                    'email_responsable':  responsable['email'],
                    'telefono_responsable': responsable['phone_number']
                }

                self.env['trafitec.responsable'].create(vals)

    def shipments_manager(self, shipment):
        records = self.env['trafitec.viajes'].search([
            ('id_fletex', '=', shipment['shipment_id'])])
        
        if records:
            for record in records:
                quotation = self.env['trafitec.cotizacion'].search([
                ('id_fletex', '=', shipment['project_id'])])

                line_quotation = self.env['trafitec.cotizaciones.linea'].search([
                    ('cotizacion_id', '=', quotation['id'])])

                driver = self.env['res.partner'].search([
                    ('driver_id_fletex', '=', shipment['user_id'])])
                vehicle = self.env['fleet.vehicle'].search([
                    ('id_fletex_truck', '=', shipment['vehicle_id'])])
                
                vehicle.write({
                    'operador_id': driver['id']
                })

                business = self.env['res.partner'].search([
                    ('id_fletex', '=', shipment['business_id'])])

                if shipment['status'] == 'finalized':
                    status = 'finalizado'
                elif shipment['status'] == 'active': 
                    status = 'enproceso'
                else :
                    status = 'enespera'

                vals = {
                    'id_fletex': shipment['shipment_id'],
                    'peso_autorizado': shipment['tons'] * 1000,
                    'asociado_id': business['id'],
                    'estado_viaje': status,
                    'peso_autorizado': shipment['tons'],
                    'peso_destino_remolque_1': shipment['tons'] * 1000,
                    'peso_destino_remolque_2': shipment['tons_full'] * 1000,
                    'tipo_lineanegocio': quotation['lineanegocio']['name'],
                    'referencia_asociado':  shipment['shipment_id'],
                    'referencia_cliente':  shipment['shipment_id']
                }
                _logger.info(record)
                record.write(vals)

                if shipment['evidences'] :
                    evidences_ids = self.env['trafitec.viajes.evidencias'].search([
                        ('linea_id','=',record['id'])
                    ])
                    for evidence in shipment['evidences'] :
                        if evidence in evidences_ids :
                            continue;
                        else :
                            vals = {
                                'linea_id': record['id'],
                                'evidencia_file': evidence,
                                'image_filename': "Evidencia de viaje {}.{}".format(record['id'],
                                                            self.find_extension_document(evidence)),
                                'name': "Evidencia de viaje"
                            }
                            self.env['trafitec.viajes.evidencias'].create(vals)

                if record['estado_viaje'] == 'finalizado' :

                    invoice = self.env['invoice.from.fletex'].search([
                            ('fletexShipmentReference', '=', shipment['shipment_id'])])

                    if not invoice :
                        if shipment['invoice_xml'] and shipment['invoice_pdf'] :
                            if len(shipment['invoice_xml']) > 0:

                                vals = {
                                    'clientId': business['id'],
                                    'shipmentId': record['id'],
                                    'fletexProjectReference': quotation['id_fletex'],
                                    'fletexShipmentReference': shipment['shipment_id'],
                                    'invoiceXml': shipment['invoice_xml'],
                                    'invoicePdf': shipment['invoice_pdf'],
                                }

                                self.env['invoice.from.fletex'].create(vals)

        else:
            quotation = self.env['trafitec.cotizacion'].search([
                ('id_fletex', '=', shipment['project_id'])])

            line_quotation = self.env['trafitec.cotizaciones.linea'].search([
                ('cotizacion_id', '=', quotation['id'])])

            business = self.env['res.partner'].search([
                ('id_fletex', '=', shipment['business_id'])])

            driver = self.env['res.partner'].search([
                ('driver_id_fletex', '=', shipment['user_id'])])

            vehicle = self.env['fleet.vehicle'].search([
                ('id_fletex_truck', '=', shipment['vehicle_id'])])
                
            currency_id = self.env['res.currency'].search([(
                                            'name', '=', 'MXN')])

            vehicle.write({
                'operador_id': driver['id']
            })
            status = 'enespera'

            if shipment['status'] == 'finalized':
                status = 'finalizado'
            elif shipment['status'] == 'active': 
                status = 'enproceso'

            vals = {
                'linea_id': line_quotation['id'],
                'id_fletex': shipment['shipment_id'],
                'moneda': currency_id['id'],
                'cliente_id': quotation['cliente']['id'],
                'origen': quotation['origen_id']['id'],
                'destino': quotation['destino_id']['id'],
                'tarifa_asociado': line_quotation['tarifa_asociado'],
                'tarifa_cliente': line_quotation['tarifa_cliente'],
                'flete_cliente': line_quotation['tarifa_cliente'] 
                                    * shipment['tons'],
                'flete_asociado': line_quotation['tarifa_asociado'] 
                                    * shipment['tons'],
                'costo_producto': quotation['costo_producto'],
                'placas_id': vehicle['id'],
                'operador_id': driver['id'],
                'celular_operador': '00000000',
                'asociado_id': business['id'],
                'celular_asociado': business['phone_representative'],
                'peso_autorizado': 1,
                'asociado_id': business['id'],
                'estado_viaje': status,
                'peso_autorizado': shipment['tons'] * 1000,
                'peso_origen_remolque_1': shipment['tons'] * 1000,
                'peso_origen_remolque_2': shipment['tons_full'] * 1000,
                'peso_convenido_remolque_1': shipment['tons'] * 1000,
                'peso_convenido_remolque_2': shipment['tons_full'] * 1000,
                'peso_destino_remolque_1': shipment['tons'] * 1000,
                'peso_destino_remolque_2': shipment['tons_full'] * 1000,
                'lineanegocio': quotation['lineanegocio']['id'],
                'tipo_lineanegocio': quotation['lineanegocio']['name'],
                'referencia_asociado':  shipment['shipment_id'],
                'referencia_cliente':  shipment['shipment_id']
            }
            self.env['trafitec.viajes'].create(vals)


    def search_record(self, model, field, value):
        """ Function used to search for an id in Odoo :
        model (string) = Model to look for
        field (string) = Field to compare
        value (string) = Value to compare with the field
        """
        record = self.env[model].search([
            (field, '=', value)], limit=1)
        if len(record) > 0:
            return record['id']
        else:
            self.save_result_sync(
                "Error en concurrencia de datos",
                "Dato alojado por FLETEX: {}".format(value),
                "Error"
            )
            return None

    def find_extension_document(self, document):
        """ function to extract extension from base64 encoded files
        document (base64 encode) = base64 encoded file
        """
        if document != None:
            document = base64.b64decode(document)
            ext = imghdr.what(None, h=document)
            if not imghdr.what(None, h=document):
                return 'pdf'
            else:
                return ext

    def save_result_sync(self, record_type, description, result):
        vals = {
            'record_type': record_type,
            'description': description,
            'result': result,
            'date': fields.Date.today()
        }

        self.env['info.sync.fletex'].create(vals)
