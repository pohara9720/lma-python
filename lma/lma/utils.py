from api.serializers import (
    AnimalSerializer,
    InventorySerializer,
    SaleSerializer,
    UserSerializer
)
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
from django.core.mail import EmailMessage, send_mail
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
from rest_framework.authtoken.models import Token
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from datetime import date, timedelta
import calendar
from smtplib import SMTPException
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
from xhtml2pdf.config.httpconfig import httpConfig
httpConfig.save_keys('nosslcheck', True)


stripe.api_key = settings.STRIPE_SECRET_KEY

# SECTION Stripe


class Stripe:
    @staticmethod
    def create_stripe_account(request):
        price_id = request.data['subscription']
        email = request.data['email']
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

        customer = stripe.Customer.create(
            name=card_name,
            email=email,
            address={
                "city": request.data['payment_city'],
                "state": request.data['payment_state'],
                "postal_code": request.data['payment_zipcode'],
                "line1": request.data['payment_street'],
                "country": "US"
            }
        )

        token = stripe.Token.create(
            card={
                "number": card_number,
                "exp_month": card_exp.split('-')[1],
                "exp_year": card_exp.split('-')[0],
                "cvc": card_cvc,
            },
        )

        stripe.Customer.create_source(
            customer['id'],
            source=token,
        )

        subscription = stripe.Subscription.create(
            customer=customer['id'],
            items=[
                {"price": price[price_id]},
            ],
        )

        account = dict()
        account['subscription'] = subscription['id']
        account['customer'] = customer['id']
        return account

    @staticmethod
    def retrieve_account(pk):
        customer = stripe.Customer.retrieve(pk)
        source = customer['default_source']
        payment_details = stripe.Customer.retrieve_source(
            customer['id'], source)
        last4 = payment_details['last4']
        exp_month = payment_details['exp_month']
        exp_year = payment_details['exp_year']

        response = {
            "id": customer['id'],
            "name": customer['name'],
            "address": {
                "street": customer['address']['line1'],
                "city": customer['address']['city'],
                "state": customer['address']['state'],
                "zipcode": customer['address']['postal_code'],
            },
            "last4": last4,
            "exp_month": exp_month,
            "exp_year": exp_year,
        }
        return response

    @staticmethod
    def update_account(request, pk):
        data = request.data
        name = data['name']
        number = data['number']
        expiration = data['expiration']
        cvc = data['cvc']
        street = data['street']
        city = data['city']
        state = data['state']
        zipcode = data['zipcode']

        customer = stripe.Customer.modify(
            pk,
            name=name,
            address={
                "city": city,
                "line1": street,
                "postal_code": zipcode,
                "state": state
            }
        )

        stripe.Customer.delete_source(
            customer['id'], customer['default_source'])

        token = stripe.Token.create(
            card={
                "number": number,
                "exp_month": expiration.split('-')[1],
                "exp_year": expiration.split('-')[0],
                "cvc": cvc,
            },
        )

        stripe.Customer.create_source(
            customer['id'],
            source=token,
        )

        result = Stripe.retrieve_account(pk)
        return result

    @staticmethod
    def retrieve_subscription(sub_id):
        subscription = stripe.Subscription.retrieve(sub_id)
        product_id = subscription['items']['data'][0]['price']['product']
        product = stripe.Product.retrieve(product_id)
        return {"subscription": subscription, "product": product}

    @staticmethod
    def update_subscription(sub_item_id, price_id):
        price = dict()
        price['FREE'] = settings.STRIPE_PRICE_FREE_TIER
        price['BASIC_MONTHLY'] = settings.STRIPE_PRICE_BASIC_TIER_MONTHLY
        price['BASIC_ANNUALLY'] = settings.STRIPE_PRICE_BASIC_TIER_ANNUALLY
        price['STANDARD_MONTHLY'] = settings.STRIPE_PRICE_STANDARD_TIER_MONTHLY
        price['STANDARD_ANNUALLY'] = settings.STRIPE_PRICE_STANDARD_TIER_ANNUALLY
        price['PROFESSIONAL_MONTHLY'] = settings.STRIPE_PRICE_PROFESSIONAL_TIER_MONTHLY
        price['PROFESSIONAL_ANNUALLY'] = settings.STRIPE_PRICE_PROFESSIONAL_TIER_ANNUALLY

        item = stripe.SubscriptionItem.modify(
            sub_item_id,
            price=price[price_id],
        )

        return item


class Util:
    @staticmethod
    def authenticate(request, db):
        token = request.META['HTTP_AUTHORIZATION'].split()[1]
        user_email = Token.objects.get(key=token).user
        if user_email:
            user = User.objects.get(email=user_email)
            serializer = UserSerializer(instance=user, context={
                'request': request})
            if db:
                return user
            else:
                return serializer.data
        else:
            print('NO USER')
            pass

    @staticmethod
    def send_email(data):
        subject = data['email_subject']
        message = data['email_body']
        recipients = data['to_email']
        from_email = settings.EMAIL_HOST_USER
        html = data.get('html')
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False,
                html_message=html
            )
        except SMTPException as e:
            print('There was an error sending an email: ', e)

    @staticmethod
    def upload_file(image_file):
        s3 = boto3.client('s3')
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        key_id = uuid.uuid4()
        file_type = image_file.name.split('.')[1]
        key = Template("$key.$type").substitute(key=key_id, type=file_type)
        s3.put_object(
            Bucket=bucket, Body=image_file, Key=key
        )
        # NEED TO BE US-EAST-1
        url = Template(
            "https://$bucket.s3.amazonaws.com/$key").substitute(bucket=bucket, key=key)
        return url

    @staticmethod
    def delete_file(url):
        s3 = boto3.client('s3')
        key = url.rpartition("/")[-1]
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        s3.delete_object(Bucket=bucket, Key=key)
        return {'status': 200}

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
            request, 'company_street', 'company_state', 'company_city', 'company_zipcode'
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

    @staticmethod
    def create_invoice_file(params: dict, download):
        sale_id = params['invoice']['id']
        template = get_template('pdf.html')
        html = template.render(params)
        buffer = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), buffer)
        pdf_value = buffer.getvalue()
        if not pdf.err:
            if download:
                response = HttpResponse(
                    pdf_value, content_type='application/pdf')
                response['Content-Disposition'] = Template(
                    'attachment; filename="invoice-$filename.pdf"').substitute(filename=sale_id)
                response.write(pdf_value)
                return response
            else:
                return html
        else:
            return HttpResponse("Error Rendering PDF", status=400)
