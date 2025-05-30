import requests
import json

from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password

from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny

from .models import Category, Customer, Order, Products,  AboutUs

from .serializers import OrderSerializer, ContactMessageSerializer
from .logger import UserLogger as Logger
from django.utils import timezone

class CartViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = "cart.html"

    def get(self, request):
        common_info = {"function": "cart_list"}
        Logger.info({"message": "Fetching cart contents"} | common_info)

        cart = request.session.get('cart', {})
        product_ids = list(cart.keys())
        products = Products.objects.filter(id__in=product_ids)

        cart_total = 0
        for product in products:
            quantity = cart.get(str(product.id), 0)
            product.quantity = quantity
            product.total = product.price * quantity
            cart_total += product.total

        context = {
            'products': products,
            'cart_total': cart_total,
            'cart_total_items': sum(cart.values())
        }

        return render(request, self.template_name, context)

    def post(self, request):
        product_id = request.POST.get('product')
        action = request.POST.get('action')
        common_info = {"function": "cart_create", "product_id": product_id, "action": action}
        Logger.info({"message": "Updating cart"} | common_info)

        cart = request.session.get('cart', {})

        if action == 'add':
            cart[product_id] = cart.get(product_id, 0) + 1
        elif action == 'remove':
            if cart.get(product_id):
                cart[product_id] -= 1
                if cart[product_id] <= 0:
                    del cart[product_id]

        request.session['cart'] = cart
        return redirect('cart')

class StoreViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'home.html'

    def get(self, request):
        common_info = {"function": "store_list"}
        Logger.info({"message": "Fetching store home view"} | common_info)
        customer_id = request.session.get('customer')
        customer = None
        if customer_id:
            customer = Customer.objects.filter(id=customer_id).first()

        cart = request.session.get('cart', {})
        request.session['cart'] = cart

        category_id = request.GET.get('category')
        query = request.GET.get('q')
        categories = Category.objects.all()

        if query:
            products = Products.objects.filter(name__icontains=query)
            
        else:
            products = Products.objects.all()
            
        return render(request, self.template_name, {
            'products': products,
            'cart_total_items': sum(cart.values()),
            'query': query,
            'customer': customer,
        }) 

    def post(self, request):
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        cart[product_id] = cart.get(product_id, 0) + quantity
        request.session['cart'] = cart

        Logger.info({"message": f"Added product {product_id} to cart", "quantity": quantity})
        return redirect('homepage')

class ProductDetailViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'home.html'

    def get(self, request, pk=None):
        common_info = {"function": "product_detail", "product_id": pk}
        Logger.info({"message": "Fetching product detail"} | common_info)

        product = get_object_or_404(Products, id=pk)
        categories = Category.objects.all()

        grouped_products = {cat.name: Products.objects.filter(category=cat) for cat in categories}
        related_products = product.category.products.exclude(id=product.id)

        cart = request.session.get('cart', {})

        return render(request, self.template_name, {
            'product': product,
            'grouped_products': grouped_products,
            'categories': categories,
            'cart_total_items': sum(cart.values()),
            'related_products': related_products
        })

class SignupViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'signup.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        postData = request.POST
        username = postData.get('username')
        phone = postData.get('phone')
        email = postData.get('email')
        password = postData.get('password')

        customer = Customer(username=username, phone=phone, email=email, password=password)
        error_message = self.validate_customer(customer)

        if not error_message:
            customer.password = make_password(customer.password)
            customer.register()
            Logger.info({"message": f"New customer signed up: {email}"})
            return redirect(f'/login/?email={email}&password={password}')
        else:
            return render(request, self.template_name, {
                'error': error_message,
                'values': {'username': username, 'phone': phone, 'email': email}
            })

    def validate_customer(self, customer):
        if not customer.username:
            return "Please enter a username"
        if len(customer.username) < 3:
            return "Username must be at least 3 characters"
        if not customer.phone or len(customer.phone) < 10:
            return "Enter a valid phone number"
        if len(customer.password) < 5:
            return "Password must be at least 5 characters"
        if len(customer.email) < 5:
            return "Email must be valid"
        return None

class LoginViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'login.html'
    return_url = None

    def get(self, request):
        LoginViewSet.return_url = request.GET.get('return_url')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        customer = Customer.objects.filter(email=email).first()

        if customer and check_password(password, customer.password):
            request.session['customer'] = customer.id
            Logger.info({"message": f"Customer {email} logged in"})
            return HttpResponseRedirect(LoginViewSet.return_url or '/')
        else:
            return render(request, self.template_name, {'error': 'Invalid email or password'})

def logout(request):
    request.session.clear()
    return redirect('login')


class CheckOutViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'checkout.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return render(request, self.template_name, {'error': 'Your cart is empty!'})

        customer_id = request.session.get('customer')
        if not customer_id:
            return redirect('login')

        customer = Customer.objects.get(id=customer_id)

        # Shipping + payment form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address1')
        city = request.POST.get('city')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip')
        payment_method = request.POST.get('payment_method')

        if not all([first_name, last_name, phone, address, city, country, zip_code, payment_method]):
            return render(request, self.template_name, {'error': 'Please fill in all required fields.'})

        total_amount = 0
        for product_id, quantity in cart.items():
            product = get_object_or_404(Products, id=product_id)
            total_amount += product.price * quantity

        if payment_method == "COD":
            for product_id, quantity in cart.items():
                product = get_object_or_404(Products, id=product_id)
                Order.objects.create(
                    customer=customer,
                    product=product,
                    data={
                        "quantity": quantity,
                        "price": product.price,
                        "address": f"{address}, {city}, {country} - {zip_code}",
                        "phone": customer.phone,
                        "payment_method": "COD",
                        "payment_status": "Unpaid",
                        "status": "Pending",
                        "date": timezone.now().date().isoformat()
                    }
                )
            request.session['cart'] = {}
            return render(request, 'orders.html', {'message': 'Order placed successfully (Cash on Delivery)'})

        elif payment_method == "Online":
            request.session['checkout'] = {
                "customer_id": customer.id,
                "address": f"{address}, {city}, {country} - {zip_code}",
                "phone": phone,
                "cart": cart,
                "total_amount": total_amount
            }
            request.session.save()
            return redirect('stripe_payment')

        else:
            return render(request, self.template_name, {'error': 'Invalid payment method selected.'})


class OrderViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'orders.html'

    def get(self, request):
        customer_id = request.session.get('customer')
        orders = Order.objects.filter(customer_id=customer_id).order_by('-created_at')
        for order in orders:
            data = order.data or {}
            data.setdefault('quantity', 0)
            data.setdefault('price', 0)
            data.setdefault('address', '')
            data.setdefault('phone', '')
            data.setdefault('date', None) 
            data.setdefault('status', '')
            data.setdefault('payment_status', '')
            data.setdefault('payment_method', '')
            data.setdefault('payment_reference', None)
            order.data = data
        serializer = OrderSerializer(orders, many=True)

        cart = request.session.get('cart', {})
        return render(request, self.template_name, {
            'orders': orders,
            'cart_total_items': sum(cart.values()),
            'orders_data': serializer.data 
        })

class BuyNowViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'checkout.html'

    def get(self, request, pk=None):
        product = get_object_or_404(Products, id=pk)
        return render(request, self.template_name, {'product': product})

    def post(self, request, pk=None):
     customer_id = request.session.get('customer')
     if not customer_id:
        return redirect('login')

     customer = Customer.objects.get(id=customer_id)
     product = get_object_or_404(Products, id=pk)

     first_name = request.POST.get('first_name')
     last_name = request.POST.get('last_name')
     phone = request.POST.get('phone') 
     address = request.POST.get('address1')
     city = request.POST.get('city')
     country = request.POST.get('country')
     zip_code = request.POST.get('zip')

     if not (first_name and last_name and address and city and country and zip_code):
        return render(request, self.template_name, {'error': 'Please fill in all shipping fields.'})

    # Assuming quantity is 1 for Buy Now
     Order.objects.create(
        customer=customer,
        product=product,
        data={
            "quantity": 1,
            "price": product.price,
            "address": f"{address}, {city}, {country} - {zip_code}",
            "phone": phone,
            "payment_method": "COD",
            "payment_status": "Unpaid",
            "status": "Pending",
            "date": timezone.now().date().isoformat()
        }
    )

     Logger.info({"message": f"Order placed by customer {customer.email} for product {product.name}"})
     return render(request, 'orders.html', {'message': 'Order placed successfully!'})

def about(request):
    about_us = AboutUs.objects.first() 
    return render(request, 'about.html', {'about_us': about_us})


class ContactViewSet(ViewSet):
    permission_classes = [AllowAny]
    template_name = 'contact.html'

    def get(self, request):
        Logger.info({"message": "Accessing Contact Page"})
        return render(request, self.template_name)

    def post(self, request):
        serializer = ContactMessageSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            Logger.info({"message": "Contact form submitted", "data": serializer.validated_data})
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('/contact/')  
        else:
            Logger.warning({"message": "Contact form submission failed", "errors": serializer.errors})
            return render(request, self.template_name, {'errors': serializer.errors})

class StripePaymentViewSet(ViewSet):
    permission_classes = [AllowAny]

    def get(self, request):
        checkout_data = request.session.get('checkout')
        if not checkout_data:
            Logger.warning({"message": "Stripe payment attempted without checkout session data"})
            return redirect('checkout')

        customer_id = checkout_data.get('customer_id')
        cart = checkout_data.get('cart')
        total_amount = checkout_data.get('total_amount')
        address = checkout_data.get('address')
        phone = checkout_data.get('phone')

        line_items = []
        for product_id, quantity in cart.items():
            product = Products.objects.get(id=product_id)
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product.name,
                    },
                    "unit_amount": int(product.price * 100),
                },
                "quantity": quantity,
            })

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=request.build_absolute_uri('/payment-success?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/payment-cancel'),
                client_reference_id=str(customer_id),
                metadata={
                    "address": address,
                    "phone": phone,
                }
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return redirect('checkout')

def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_id = session.get('client_reference_id')
        metadata = session.get('metadata', {})
        address = metadata.get('address', '')
        phone = metadata.get('phone', '')

        customer = Customer.objects.filter(id=customer_id).first()

        # Retrieve line items from Stripe API
        line_items = stripe.checkout.Session.list_line_items(session['id'])

        for item in line_items:
            product_name = item.price.product.name if item.price and item.price.product else None
            product = Products.objects.filter(name=product_name).first()
            if not product:
                continue

            quantity = item.quantity

            Order.objects.create(
                customer=customer,
                product=product,
                data={
                    "quantity": quantity,
                    "price": product.price,
                    "address": address,
                    "phone": phone,
                    "payment_method": "Online",
                    "payment_status": "Paid",
                    "status": "Confirmed",
                    "date": timezone.now().date().isoformat(),
                    "payment_reference": session.get('payment_intent')
                }
            )
    return HttpResponse(status=200)

def payment_success(request):
    request.session['cart'] = {}
    request.session['checkout'] = {}
    return render(request, 'payment_success.html')

def payment_cancel(request):
    return render(request, 'payment_cancel.html')