# Copyright 2020 Traceable, Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Configuration for crapi application
"""
import django
import sys
from django.apps import AppConfig
import bcrypt
from django.utils import timezone
from django.db import models
from django.db import connection, transaction
import logging

MAX_PREDEF_MECH_REPORTS:int = 6 # The maximum predefined reports to generate
MAX_PREDEF_REPORTS_PER_USER:int = 2

logger = logging.getLogger()


def create_products():
    from crapi.shop.models import Product
    product_details_all = [
        {
            'name': 'Seat',
            'price': 10,
            'image_url': 'images/seat.svg'
        },
        {
            'name': 'Wheel',
            'price': 10,
            'image_url': 'images/wheel.svg'
        }
    ]
    for product_details in product_details_all:
        if Product.objects.filter(name=product_details['name']).exists():
            continue
        product = Product.objects.create(
            name=product_details['name'],
            price=float(product_details['price']),
            image_url=product_details['image_url']
        )

def create_mechanics():
    from user.models import User, UserDetails
    from crapi.mechanic.models import Mechanic
    mechanic_details_all = [
        {
            'name': 'Mechanic One',
            'email': 'mechanic.one@example.com',
            'number': '9051892421',
            'password': 'Mechanic1One',
            'mechanic_code': 'TRAC_MECH1'
        },
        {
            'name': 'Mechanic Two',
            'email': 'mechanic.two@example.com',
            'number': '8056897231',
            'password': 'Mechanic2Two',
            'mechanic_code': 'TRAC_MECH2'
        },
    ]
    for mechanic_details in mechanic_details_all:
        uset = User.objects.filter(email=mechanic_details['email'])
        if not uset.exists():
            try:
                cursor = connection.cursor()
                cursor.execute("select nextval('user_login_id_seq')")
                result = cursor.fetchone()
                user_id = result[0]
            except Exception as e:
                logger.error("Failed to fetch user_login_id_seq"+str(e))
                user_id = 1

            user = User.objects.create(
                id=user_id,
                email=mechanic_details['email'],
                number=mechanic_details['number'],
                password=bcrypt.hashpw(
                    mechanic_details['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode(),
                role=User.ROLE_CHOICES.MECH,
                created_on=timezone.now()
            )
        else:
            user = uset.first()
            
        if Mechanic.objects.filter(mechanic_code=mechanic_details['mechanic_code']):
            continue
        
        Mechanic.objects.create(
            mechanic_code=mechanic_details['mechanic_code'],
            user=user
        )
        try:
            cursor = connection.cursor()
            cursor.execute("select nextval('user_details_id_seq')")
            result = cursor.fetchone()
            user_details_id = result[0]
        except Exception as e:
            logger.error("Failed to fetch user_details_id_seq"+str(e))
            user_details_id = 1
        UserDetails.objects.create(
            id=user_details_id,
            available_credit=0,
            name=mechanic_details['name'],
            status='ACTIVE',
            user=user
        )



def create_reports():
    import random
    import sys
    import textwrap
    from user.models import User, UserDetails, Vehicle
    from crapi.mechanic.models import Mechanic, ServiceRequest
    from django.utils import timezone
    
    if (ServiceRequest.objects.all().count() >= MAX_PREDEF_MECH_REPORTS):
        return
    
    mechanics = Mechanic.objects.all()
    users = User.objects.all()

    numGen:int = 0
    for user in users:
        try:
            if (numGen >= MAX_PREDEF_MECH_REPORTS): break

            for i in range(MAX_PREDEF_REPORTS_PER_USER):
                user_vehicles = Vehicle.objects.filter(owner=user)
                vehicle = random.choice(user_vehicles)
                mechanic = random.choice(mechanics)
                status = random.choice(ServiceRequest.STATUS_CHOICES)[0]
                issue = random.choice(ServiceRequest.ISSUES)
                vehicle_model = vehicle.vehicle_model
                vehicle_company = vehicle_model.vehiclecompany
                user_detail = UserDetails.objects.filter(user=user).first()

                service_request = ServiceRequest.objects.create(
                    vehicle=vehicle,
                    mechanic=mechanic,
                    problem_details=textwrap.dedent("""\
                        My car {} - {} is having {} issues.
                        Can you give me a call on my mobile {},
                        Or send me an email at {} 
                        Thanks,
                        {}.
                        """.format(
                            vehicle_company.name, 
                            vehicle_model.model,
                            issue,
                            user.number, 
                            user.email, 
                            user_detail.name)
                    ),
                    status=status,
                    created_on=timezone.now()
                )
                
                service_request.save()
                numGen += 1 # Ensure we limit the number of resports created

        except Exception as e:
            print(sys.exc_info()[0])
            logger.error("Failed to create report: "+str(e))   
        

def create_orders_for_user(user: str):
    """Create two orders for the specified user"""
    from .shop.models import Order, Product
    from user.models import User

    user = User.objects.get(email=user)

    userOrders = Order.objects.filter(user=user)
    if userOrders.exists():
        return

    Order.objects.create(
        user=user,
        product=Product.objects.get(id=1),
        quantity=1,
        created_on=timezone.now(),
    )

    Order.objects.create(
        user=user,
        product=Product.objects.get(id=2),
        quantity=1,
        created_on=timezone.now(),
    )

    return



def create_orders():
    """Pre-populuate orders for the two pre-defined users"""
    users = ["victim.one@example.com", "victim.two@example.com"]
    create_orders_for_user(user=users[0])
    create_orders_for_user(user=users[1])



class CRAPIConfig(AppConfig):
    """
    Stores all meta data of crapi application
    """
    name = 'crapi'

    def ready(self):
        if not 'runserver' in sys.argv:
            return
        """
        Pre-populate mechanic model and product model
        :return: None
        """
        try:
            create_products()
        except Exception as e:
            logger.error("Cannot Pre Populate Products: "+str(e))
        try:
            create_mechanics()
        except Exception as e:
            logger.error("Cannot Pre Populate Mechanics: "+str(e))
        try:
            create_reports()
        except Exception as e:
            logger.error("Cannot Pre Populate Reports: "+str(e))

        try:
            create_orders()
        except Exception as e:
            logger.error("Cannot Pre Populate Orders: " + str(e))
