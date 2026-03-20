from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    person = models.CharField(max_length=100)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=[
            ('Active', 'Active'),
            ('Closed', 'Closed')
        ],
        default='Active'
    )

    def progress(self):
        if self.total_amount == 0:
            return 0
        return int((self.paid_amount / self.total_amount) * 100)

    def remaining(self):
        return self.total_amount - self.paid_amount

    def __str__(self):
        return self.person
        
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)