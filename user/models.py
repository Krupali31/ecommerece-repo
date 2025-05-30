from django.db import models
import datetime
from django.utils import timezone


class Category(models.Model):
    """
    Model representing a product category.

    Attributes:
        name (str): The name of the category, e.g., "Electronics", "Clothing".

    Methods:
        __str__(): Returns the name of the category.
    """
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Customer(models.Model):
    """
    Model representing a customer.

    Attributes:
        username (str): The unique username for the customer. Default is 'guest_user'.
        phone (str): The phone number of the customer.
        email (str): The unique email address of the customer.
        password (str): The hashed password of the customer.

    Methods:
        register(): Registers (saves) the customer instance to the database.
        __str__(): Returns the username of the customer.
    """
    username = models.CharField(max_length=50, unique=True, default='guest_user')
    phone = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def register(self):
        """Registers (saves) the customer instance to the database."""
        self.save()

    def __str__(self):
        return self.username


class Products(models.Model):
    """
    Model representing a product in the store.

    Attributes:
        name (str): The name of the product.
        price (int): The price of the product.
        category (ForeignKey): The category to which the product belongs.
        description (str): A brief description of the product.
        image (ImageField): The image representing the product.

    Methods:
        __str__(): Returns the name of the product.
    """
    name = models.CharField(max_length=60)
    price = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=250, default='', blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Model representing a customer order.

    Attributes:
        product (ForeignKey): The product ordered.
        customer (ForeignKey): The customer who placed the order.
        data (JSONField): Additional order-related data.
        created_at (datetime): Timestamp when the order was created.
        updated_at (datetime): Timestamp when the order was last updated.

    Methods:
        __str__(): Returns a readable identifier for the order.
    """
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    data = models.JSONField()

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} by {self.customer}"


class AboutUs(models.Model):
    """
    Model representing the 'About Us' section of the site.

    Attributes:
        title (str): The title for the 'About Us' section (default is "About Us").
        content (str): The content/text for the 'About Us' section.

    Methods:
        __str__(): Returns the title of the 'About Us' section.
    """
    title = models.CharField(max_length=255, default="About Us")
    content = models.TextField()

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """
    Model representing a contact form message sent by a user.

    Attributes:
        name (str): The name of the user sending the message.
        email (str): The email address of the user.
        message (str): The content of the message.
        created_at (datetime): The timestamp when the message was submitted.

    Methods:
        __str__(): Returns a summary of the sender and email.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} ({self.email})"