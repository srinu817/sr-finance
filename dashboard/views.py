from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.conf import settings
# from django.core.mail import send_mail
from django.contrib import messages
from django.core.cache import cache

from .models import Expense, Income, Loan
from .forms import LoanForm

import calendar
import random,requests


# ========================= MAIL ========================= #

# def send_user_mail(user, subject, message):
#     if not user.email:
#         print("❌ No email found for user")
#         return

#     try:
#         print("🔥 MAIL FUNCTION CALLED")

#         send_mail(
#             subject,
#             message,
#             settings.DEFAULT_FROM_EMAIL,
#             [user.email],
#             fail_silently=False,   # ✅ IMPORTANT FIX
#         )

#         print("✅ MAIL SENT SUCCESSFULLY")

#     except Exception as e:
#         print("❌ MAIL ERROR:", e)
# def send_user_mail(user, subject, message):
#     # 🔥 TEMP FIX: disable email to avoid Render crash
#     print("⚠ EMAIL DISABLED (Render issue)")
    
#     if user and user.email:
#         print("➡ TO:", user.email)
#     else:
#         print("➡ No email found")

#     print("➡ SUBJECT:", subject)
#     print("➡ MESSAGE:", message)

#     return
# import requests
# from django.conf import settings

# def send_user_mail(user, subject, message):
#     if not user.email:
#         print("❌ No email")
#         return

#     try:
#         print("🔥 Sending email via SendGrid API")

#         url = "https://api.sendgrid.com/v3/mail/send"

#         headers = {
#             "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
#             "Content-Type": "application/json"
#         }

#         data = {
#             "personalizations": [
#                 {
#                     "to": [{"email": user.email}],
#                     "subject": subject
#                 }
#             ],
#             "from": {"email": settings.DEFAULT_FROM_EMAIL},
#             "content": [
#                 {
#                     "type": "text/plain",
#                     "value": message
#                 }
#             ]
#         }

#         response = requests.post(url, headers=headers, json=data)

#         print("STATUS:", response.status_code)
#         print("RESPONSE:", response.text)

#     except Exception as e:
#         print("❌ Email Error:", e)
# def send_user_mail(user, subject, message):
#     if not user.email:
#         print("❌ No email")
#         return

#     try:
#         url = "https://api.brevo.com/v3/smtp/email"

#         headers = {
#             "accept": "application/json",
#             "api-key": settings.BREVO_API_KEY,
#             "content-type": "application/json"
#         }

#         data = {
#             "sender": {"email": settings.DEFAULT_FROM_EMAIL},
#             "to": [{"email": user.email}],
#             "subject": subject,
#             "textContent": message
#         }

#         response = requests.post(
#             url,
#             headers=headers,
#             json=data,
#             timeout=10   # 🔥 add this line
#         )

#         print("📩 STATUS:", response.status_code)
#         print("📩 RESPONSE:", response.text)
#         print("API:", settings.BREVO_API_KEY)
#     except requests.exceptions.Timeout:
#         print("❌ Email timeout")

#     except Exception as e:
#         print("❌ Email Error:", e)
# def send_user_mail(user, subject, message):
#     if not user.email:
#         print("❌ No email")
#         return False   # 👈 important

#     try:
#         url = "https://api.brevo.com/v3/smtp/email"

#         headers = {
#             "accept": "application/json",
#             "api-key": settings.BREVO_API_KEY,
#             "content-type": "application/json"
#         }

#         data = {
#             "sender": {"email": settings.DEFAULT_FROM_EMAIL},
#             "to": [{"email": user.email}],
#             "subject": subject,
#             "textContent": message
#         }

#         response = requests.post(
#             url,
#             headers=headers,
#             json=data,
#             timeout=10
#         )

#         print("📩 STATUS:", response.status_code)
#         print("📩 RESPONSE:", response.text)

#         if response.status_code == 201:
#             return True   # ✅ SUCCESS
#         else:
#             return False  # ❌ FAIL

#     except requests.exceptions.Timeout:
#         print("❌ Email timeout")
#         return False

#     except Exception as e:
#         print("❌ Email Error:", e)
#         return False


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Sum

from .models import Expense, Income, Loan
from .utils import send_mail_async

import random


# ================= OTP ================= #

def otp_login(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "User not found ❌")
            return redirect("login")

        otp = str(random.randint(100000, 999999))

        cache.set(f"otp_{email}", otp, timeout=300)
        request.session['otp_email'] = email

        html = f"""
        <h2>SR Finance 🔐</h2>
        <p>Your OTP is:</p>
        <h1>{otp}</h1>
        <p>Valid for 5 minutes</p>
        """

        send_mail_async(user, "Your OTP Code", html)

        messages.success(request, "OTP sent successfully ✅")
        return render(request, "dashboard/login.html", {"otp_sent": True})

    return render(request, "dashboard/login.html")


def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        email = request.session.get("otp_email")

        if not email:
            return redirect("login")

        stored_otp = cache.get(f"otp_{email}")

        if stored_otp == otp_input:
            user = User.objects.get(email=email)
            login(request, user)

            cache.delete(f"otp_{email}")
            request.session.pop('otp_email', None)

            return redirect("dashboard")

        messages.error(request, "Invalid OTP ❌")
        return redirect("login")

    return redirect("login")


# ================= AUTH ================= #

def login_view(request):
    return render(request, "dashboard/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists ❌")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists ❌")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)

        html = "<h3>Welcome to SR Finance 🎉</h3><p>Your account created successfully</p>"
        send_mail_async(user, "Welcome", html)

        return redirect("dashboard")

    return render(request, "dashboard/signup.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ================= DASHBOARD ================= #

@login_required
def dashboard_view(request):
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_loan = Loan.objects.filter(user=request.user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    wallet = total_income - total_expense - total_loan

    return render(request, "dashboard/dashboard.html", {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_loan": total_loan,
        "wallet": wallet
    })


# ================= EXPENSE ================= #

@login_required
def expense_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")

        if not title or not amount:
            messages.error(request, "Fill all fields ❌")
            return redirect("expenses")

        expense = Expense.objects.create(
            user=request.user,
            title=title,
            amount=amount
        )

        html = f"<h3>Expense Added 💸</h3><p>₹{expense.amount} spent on {expense.title}</p>"
        send_mail_async(request.user, "Expense Added", html)

        messages.success(request, "Expense added successfully ✅")
        return redirect("expenses")

    expenses = Expense.objects.filter(user=request.user)
    return render(request, "dashboard/expenses.html", {"expenses": expenses})


# ================= INCOME ================= #

@login_required
def income_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")

        if not title or not amount:
            messages.error(request, "Fill all fields ❌")
            return redirect("income")

        income = Income.objects.create(
            user=request.user,
            title=title,
            amount=amount
        )

        html = f"<h3>Income Added 💰</h3><p>₹{income.amount} received from {income.title}</p>"
        send_mail_async(request.user, "Income Added", html)

        messages.success(request, "Income added successfully 💰")
        return redirect("income")

    incomes = Income.objects.filter(user=request.user)
    return render(request, "dashboard/income.html", {"incomes": incomes})


# ================= LOAN ================= #

@login_required
def loans_view(request):
    loans = Loan.objects.filter(user=request.user)
    return render(request, "dashboard/loans.html", {"loans": loans})


@login_required
def add_loan(request):
    if request.method == "POST":
        person = request.POST.get("person")
        total_amount = request.POST.get("total_amount")

        if not person or not total_amount:
            messages.error(request, "Fill all fields ❌")
            return redirect("loans")

        loan = Loan.objects.create(
            user=request.user,
            person=person,
            total_amount=total_amount
        )

        html = f"<h3>Loan Added 📄</h3><p>₹{loan.total_amount} given to {loan.person}</p>"
        send_mail_async(request.user, "Loan Added", html)

        messages.success(request, "Loan added successfully 📄")
        return redirect("loans")

    return render(request, "dashboard/add_loan.html")


@login_required
def delete_loan(request, id):
    loan = get_object_or_404(Loan, id=id, user=request.user)
    loan.delete()
    return redirect("loans")

@login_required
def mark_paid(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id, user=request.user)

    loan.paid_amount = loan.total_amount
    loan.status = "Closed"
    loan.save()

    cache.delete(f"dashboard_{request.user.id}")

    return redirect("loans")

# ========================= REPORTS ========================= #
@login_required
def reports(request):

    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0

    # ✅ FIXED (loan amount field change)
    total_loan = Loan.objects.filter(user=request.user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    wallet = total_income - total_expense - total_loan

    # ✅ Monthly
    monthly_expenses = (
        Expense.objects.filter(user=request.user)
        .annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    for m in monthly_expenses:
        m['month_name'] = calendar.month_name[m['month']]
        m['income'] = Income.objects.filter(
            user=request.user,
            date__month=m['month']
        ).aggregate(Sum('amount'))['amount__sum'] or 0

    # ✅ LEDGER (NEW)
    from itertools import chain

    incomes = Income.objects.filter(user=request.user).values('date', 'title', 'amount')
    expenses = Expense.objects.filter(user=request.user).values('date', 'title', 'amount')

    for i in incomes:
        i['type'] = 'income'

    for e in expenses:
        e['type'] = 'expense'

    ledger = sorted(
        chain(incomes, expenses),
        key=lambda x: x['date'],
        reverse=True
    )

    if request.method == "POST":

        if "send_email" in request.POST:
            message = f"""
Income: ₹{total_income}
Expense: ₹{total_expense}
Loans: ₹{total_loan}
Wallet: ₹{wallet}
"""
            send_user_mail(request.user, "Your Report 📊", message)
            messages.success(request, "Report sent to your email ✅")

    context = {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_loan": total_loan,
        "wallet": wallet,
        "monthly_expenses": monthly_expenses,
        "ledger": ledger
    }

    return render(request, "dashboard/reports.html", context)
# ========================= PROFILE ========================= #

@login_required
def profile_view(request):

    if request.method == "POST":

        # Profile update
        if "username" in request.POST:
            request.user.username = request.POST.get("username")
            request.user.email = request.POST.get("email")
            request.user.save()

            messages.success(request, "Profile updated successfully ✅")
            return redirect("profile")

        # Password update
        if "password" in request.POST:
            password = request.POST.get("password")

            if password:
                request.user.set_password(password)
                request.user.save()

                messages.success(request, "Password updated 🔐")
                return redirect("login")

    return render(request, "dashboard/profile.html")


# ========================= DELETE ACCOUNT ========================= #

@login_required
def delete_account(request):

    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()

        messages.success(request, "Account deleted successfully ❌")
        return redirect("login")