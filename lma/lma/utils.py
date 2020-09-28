from django.core.mail import EmailMessage
import boto3
from django.conf import settings
from string import Template
import uuid
import threading
import stripe
import io
from django.http import HttpResponse
# from reportlab.pdfgen import canvas
from reportlab.platypus import Table
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors


from api.models import (
    User,
    Company,
    Address,
    Animal,
    Inventory,
    Task,
    InvoiceItem,
    Sale
)

from api.serializers import (
    AnimalSerializer,
    InventorySerializer,
    SaleSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

# SECTION Stripe


class Stripe:
    @staticmethod
    def create_stripe_account(request):
        price_id = request.data['subscription']
        price = dict()
        price['FREE'] = settings.STRIPE_PRICE_FREE_TIER
        price['BASIC_MONTHLY'] = settings.STRIPE_PRICE_BASIC_TIER_MONTHLY
        price['BASIC_ANNUALLY'] = settings.STRIPE_PRICE_BASIC_TIER_ANNUALLY
        price['STANDARD_MONTHLY'] = settings.STRIPE_PRICE_STANDARD_TIER_MONTHLY
        price['STANDARD_ANNUALLY'] = settings.STRIPE_PRICE_STANDARD_TIER_ANNUALLY
        price['PROFESSIONAL_MONTHLY'] = settings.STRIPE_PRICE_PROFESSIONAL_TIER_MONTHLY
        price['PROFESSIONAL_ANNUALLY'] = settings.STRIPE_PRICE_PROFESSIONAL_TIER_ANNUALLY
        card_name = request.data['payment_name']
        card_number = request.data['payment_card']
        card_exp = request.data['payment_expiration']
        card_cvc = request.data['payment_cvc']
        address = {
            "city": request.data['payment_city'],
            "state": request.data['payment_state'],
            "postal_code": request.data['payment_zip'],
            "line1": request.data['payment_street'],
            "country": "US"
        },

        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": card_number,
                "exp_month": card_exp.split('-')[1],
                "exp_year": card_exp.split('-')[0],
                "cvc": card_cvc,
            },
            billing_details={
                "address": address,
                "name": card_name
            }
        )
        customer = stripe.Customer.create(
            name=card_name,
            payment_method=payment_method['id'],
            address=address
        )
        subscription = stripe.Subscription.create(
            customer=customer['id'],
            items=[
                {"price": price[price_id]},
            ],
        )
        account = dict()
        account['subscription'] = subscription
        account['customer'] = customer
        return account


class EmailThread(threading.Thread):

    def __init__(self, email):

        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


class Util:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        EmailThread(email).start()

    @staticmethod
    def upload_file(image_file):
        s3 = boto3.client('s3')
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        key_id = uuid.uuid4
        file_type = image_file.name.split('.')[1]
        key = Template("$key_id.$type").substitute(key=key_id, type=file_type)
        s3.put_object(
            Bucket=bucket, Body=image_file, Key=key
        )
        # NEED TO BE US-EAST-1
        url = Template(
            "https://$bucket.s3.amazonaws.com/$key").substitute(bucket=bucket, key=key)
        return url

    @staticmethod
    def save_address(request, street, state, city, zipcode):
        address = Address.objects.create(
            street=request.data[street], state=request.data[state], city=request.data[city], zipcode=request.data[zipcode])
        return address

    @staticmethod
    def save_company(request):
        stripe_info = Stripe.create_stripe_account(request)
        name = request.data['company_name']
        email = request.data['email']
        payment_info = stripe_info['customer']
        subscription = stripe_info['subscription']
        company_logo = Util.upload_file(request.data['company_logo'])
        company_address = Util.save_address(
            request, 'company_street', 'company_state', 'company_city', 'company_zip'
        )

        company = Company.objects.create(
            name=name, email=email, logo=company_logo,
            subscription=subscription, payment_info=payment_info, address=company_address
        )
        return company

    @staticmethod
    def get_pdf_data(request, type):
        animal_list = Animal.objects.all().values()
        inventory_list = Inventory.objects.all().values()
        sale_list = Sale.objects.all().values()
        animal_headers = ['id', 'name', 'type', 'sub type', 'header image', 'profile image',
                          'tag #', 'registration #', 'dob', 'breed', 'father', 'mother', 'attachment']
        inventory_headers = ['id', 'category', 'cost', 'tank #',
                             'canister #', 'top id', 'father', 'mother', 'units']
        sales_headers = ['id', 'number', 'due date', 'issue date', 'title',
                         'billed to name', 'billed to address', 'email', 'status', 'phone']

        def row(list):
            values = []
            for item in list:
                item['id'] = str(item['id'])
                value = item.values()
                values.append(value)
            return values

        inventory_table_data = [
            inventory_headers,
            *row(inventory_list),
        ]

        sales_table_data = [
            sales_headers,
            *row(sale_list),
        ]

        animal_table_data = [
            animal_headers,
            *row(animal_list),
        ]
        if type == 'animal':
            return animal_table_data
        elif type == 'inventory':
            return inventory_table_data
        else:
            return sales_table_data

    @staticmethod
    def export_pdf(request, filename, data):
        style = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]
        buffer = io.BytesIO()
        pdf = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        table = Table(data, style=style)
        pdf.build([table])
        pdf_value = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = Template(
            'attachment; filename="$filename"').substitute(filename=filename)

        response.write(pdf_value)
        return response
