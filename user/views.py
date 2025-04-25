from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView
from .models import Category, Customer, Order, Products,  AboutUs
import requests
from django.conf import settings

class CartView(APIView):
    def get(self, request):
        cart = request.session.get('cart', {})
        product_ids = list(cart.keys())
        products = Products.objects.filter(id__in=product_ids)

        cart_total = 0
        for product in products:
            quantity = cart.get(str(product.id), 0)
            product.quantity = quantity
            product.total = product.price * quantity
            cart_total += product.total

        return render(request, 'cart.html', {
            'products': products,
            'cart_total': cart_total,
            'cart_total_items': sum(cart.values())
        })

    def post(self, request):
        product_id = request.POST.get('product')
        action = request.POST.get('action')
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


class StoreView(APIView):
    def get(self, request):
        cart = request.session.get('cart', {})
        request.session['cart'] = cart

        category_id = request.GET.get('category')
        query = request.GET.get('q')
        categories = Category.objects.all()

        if query:
            products = Products.objects.filter(name__icontains=query)
            grouped_products = {'Search Results': products}
        elif category_id:
            products = Products.objects.filter(category_id=category_id)
            category = Category.objects.get(id=category_id)
            grouped_products = {category.name: products}
        else:
            grouped_products = {}
            for category in categories:
                grouped_products[category.name] = Products.objects.filter(category=category)

        return render(request, 'home.html', {
            'grouped_products': grouped_products,
            'categories': categories,
            'cart_total_items': sum(cart.values()),
            'query': query
        })

    def post(self, request):
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})

        cart[product_id] = cart.get(product_id, 0) + quantity
        request.session['cart'] = cart
        return redirect('homepage')


def product_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    categories = Category.objects.all()
    grouped_products = {}
    for category in categories:
        grouped_products[category.name] = Products.objects.filter(category=category)

    cart = request.session.get('cart', {})
    return render(request, 'home.html', {
        'product': product,
        'grouped_products': grouped_products,
        'categories': categories,
        'cart_total_items': sum(cart.values())
    })

class Signup(APIView):
    def get(self, request):
        return render(request, 'signup.html')

    def post(self, request):
        postData = request.POST
        username = postData.get('username')
        phone = postData.get('phone')
        email = postData.get('email')
        password = postData.get('password')

        customer = Customer(username=username, phone=phone, email=email, password=password)
        error_message = self.validateCustomer(customer)

        if not error_message:
            customer.password = make_password(customer.password)
            customer.register()
            return redirect(f'/login/?email={email}&password={password}')
        else:
            return render(request, 'signup.html', {
                'error': error_message,
                'values': {'username': username, 'phone': phone, 'email': email}
            })

    def validateCustomer(self, customer):
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


class Login(APIView):
    return_url = None

    def get(self, request):
        Login.return_url = request.GET.get('return_url')
        return render(request, 'login.html')

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        customer = Customer.objects.filter(email=email).first()

        if customer and check_password(password, customer.password):
            request.session['customer'] = customer.id
            return HttpResponseRedirect(Login.return_url or '/')
        else:
            return render(request, 'login.html', {'error': 'Invalid email or password'})


def logout(request):
    request.session.clear()
    return redirect('login')


class CheckOut(APIView):
    def get(self, request):
        return render(request, 'checkout.html')

    def post(self, request):
        cart = request.session.get('cart', {})
        if not cart:
            return render(request, 'checkout.html', {'error': 'Your cart is empty!'})

        customer_id = request.session.get('customer')
        if not customer_id:
            return redirect('login')

        customer = Customer.objects.get(id=customer_id)

        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address1')
        city = request.POST.get('city')
        province = request.POST.get('province')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip')

        if not (first_name and last_name and address and city and country and zip_code):
            return render(request, 'checkout.html', {'error': 'Please fill in all shipping fields.'})

        for product_id, quantity in cart.items():
            product = get_object_or_404(Products, id=product_id)
            Order.objects.create(
                customer=customer,
                product=product,
                price=product.price,
                quantity=quantity,
                address=f"{address}, {city}, {country} - {zip_code}",
                phone=customer.phone,
                payment_method='COD', 
                payment_status='Unpaid'
            )

        request.session['cart'] = {}

        return render(request, 'orders.html')

class OrderView(APIView):
    def get(self, request):
        customer_id = request.session.get('customer')
        orders = Order.objects.filter(customer_id=customer_id).order_by('-date')
        cart = request.session.get('cart', {})
        return render(request, 'orders.html', {
            'orders': orders,
            'cart_total_items': sum(cart.values())
        })


class BuyNowView(APIView):
    def get(self, request, product_id):
        product = get_object_or_404(Products, id=product_id)
        return render(request, 'buy_now_checkout.html', {'product': product})

    def post(self, request, product_id):
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')
        upi_id = request.POST.get('upi_id')
        card_number = request.POST.get('card_number')

        if not address or not phone:
            return render(request, 'buy_now_checkout.html', {
                'product': Products.objects.get(id=product_id),
                'error': 'All fields are required.'
            })

        if payment_method == 'UPI' and not upi_id:
            return render(request, 'buy_now_checkout.html', {'error': 'Please enter UPI ID'})
        if payment_method == 'Card' and not card_number:
            return render(request, 'buy_now_checkout.html', {'error': 'Please enter Card Number'})

        payment_status = 'Paid' if payment_method in ['UPI', 'Card'] else 'Unpaid'
        customer_id = request.session.get('customer')

        if customer_id:
            customer = Customer.objects.get(id=customer_id)
        else:
            customer = Customer.objects.create(
                username=f"guest_{name}",
                phone=phone,
                email=f"guest_{phone}@guest.com",
                password=make_password("guest123")
            )

        product = get_object_or_404(Products, id=product_id)
        Order.objects.create(
            customer=customer,
            product=product,
            price=product.price,
            address=address,
            phone=phone,
            quantity=1,
            payment_method=payment_method,
            payment_status=payment_status
        )

        return redirect('orders')


def about(request):
    about_us = AboutUs.objects.first() 
    return render(request, 'about.html', {'about_us': about_us})