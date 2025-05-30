from django.urls import path
from . import views
from .views import (
    StoreViewSet, SignupViewSet, LoginViewSet, logout, CheckOutViewSet,
    OrderViewSet, CartViewSet, BuyNowViewSet, ProductDetailViewSet, about, ContactViewSet,StripePaymentViewSet,
    stripe_webhook,
    payment_success,
    payment_cancel,
)

urlpatterns = [
    path('', StoreViewSet.as_view({'get': 'get', 'post': 'post'}), name='homepage'),

    path('signup/', SignupViewSet.as_view({'get': 'get', 'post': 'post'}), name='signup'),

    path('login/', LoginViewSet.as_view({'get': 'get', 'post': 'post'}), name='login'),

    path('logout/', logout, name='logout'),

    path('checkout/', CheckOutViewSet.as_view({'get': 'get', 'post': 'post'}), name='checkout'),

    path('orders/', OrderViewSet.as_view({'get': 'get'}), name='orders'),

    path('cart/', CartViewSet.as_view({'get': 'get', 'post': 'post'}), name='cart'),

    path('buy_now/<int:pk>/', BuyNowViewSet.as_view({'get': 'get', 'post': 'post'}), name='buy_now'),

    path('product/<int:pk>/', ProductDetailViewSet.as_view({'get': 'get'}), name='product_detail'),

    path('about/', views.about, name='about'),

    path('contact/', ContactViewSet.as_view({'get': 'get', 'post': 'post'}), name='contact'),

    path('stripe-payment/', StripePaymentViewSet.as_view({'get': 'get'}), name='stripe_payment'),

    path('payment-success/', payment_success, name='payment-success'),
    
    path('payment-cancel/', payment_cancel, name='payment-cancel'),

    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
]
