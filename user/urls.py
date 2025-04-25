from django.urls import path
from . import views 
from .views import (
    StoreView, Signup, Login, logout, CheckOut, OrderView,CartView,BuyNowView, product_detail,about
)

urlpatterns = [
    path('', StoreView.as_view(), name='homepage'),
    path('signup/', Signup.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    path('checkout/', CheckOut.as_view(), name='checkout'),
    path('orders/', OrderView.as_view(), name='orders'),
    path('cart/', CartView.as_view(), name='cart'),
    path('buy_now/<int:product_id>/', BuyNowView.as_view(), name='buy_now'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('about/', views.about, name='about'),
]
