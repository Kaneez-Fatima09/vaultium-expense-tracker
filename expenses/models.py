from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Wallet(models.Model):
    ACCOUNT_TYPES = (
        ('bank', 'Bank Account'),
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='bank')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (₹{self.balance})"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.amount}"

class FeedbackSupport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.email} - {self.subject}"

class PersonalVault(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_items')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='vault_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vault Item: {self.title} ({self.user.username})"

# Updated UserVaultProfile with PIN setup & Security Question for Forgot PIN
class UserVaultProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vault_profile')
    vault_pin = models.CharField(max_length=128, blank=True, null=True)  # Initially empty
    security_question = models.CharField(max_length=255, blank=True, null=True)  # e.g., Favorite Pet / City
    security_answer = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Vault Profile: {self.user.username}"