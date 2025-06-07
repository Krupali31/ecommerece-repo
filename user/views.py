from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth.hashers import check_password, make_password

from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny

from .models import Category, Customer, Order, Products,  AboutUs
import requests
from django.conf import settings

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

class OrderView(APIView):
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