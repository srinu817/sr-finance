from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache

from .models import Expense, Income, Loan

import calendar
import random
import requests
from datetime import datetime


# ========================= MAIL (BREVO API) ========================= #

def send_user_mail(user, subject, message):
    if not user.email:
        print("❌ No email")
        return

    try:
        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json"
        }

        data = {
            "sender": {
                "email": settings.DEFAULT_FROM_EMAIL,
                "name": "SR Finance"
            },
            "to": [{"email": user.email}],
            "subject": subject,
            "textContent": message
        }

        response = requests.post(url, headers=headers, json=data, timeout=10)

        print("📩 STATUS:", response.status_code)
        print("📩 RESPONSE:", response.text)

    except requests.exceptions.Timeout:
        print("❌ Email timeout error")

    except Exception as e:
        print("❌ Email Error:", e)


# ========================= AUTH ========================= #

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        attempts = cache.get(f"login_attempts_{username}", 0)
        if attempts >= 5:
            return render(request, "dashboard/login.html", {
                "error": "Too many attempts. Try later ❌"
            })

        try:
            user_obj = User.objects.get(email=username)
            username = user_obj.username
        except User.DoesNotExist:
            pass

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            cache.delete(f"login_attempts_{username}")
            return redirect("dashboard")
        else:
            cache.set(f"login_attempts_{username}", attempts + 1, timeout=300)
            return render(request, "dashboard/login.html", {
                "error": "Invalid credentials ❌"
            })

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
            messages.error(request, "Email already registered ❌")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)

        send_user_mail(user, "Welcome 🎉", "Account created successfully!")

        return redirect("dashboard")

    return render(request, "dashboard/signup.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# ========================= OTP ========================= #

def otp_login(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "dashboard/login.html", {"error": "User not found"})

        otp = str(random.randint(100000, 999999))

        cache.set(f"otp_{email}", otp, timeout=300)
        request.session['otp_email'] = email

        message = f"""
Hello {user.username},

Your OTP is: {otp}

Valid for 5 minutes.
Do not share this.

- SR Finance
"""

        send_user_mail(user, "Your OTP 🔐", message)

        return render(request, "dashboard/login.html", {"otp_sent": True})

    return redirect("login")


def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        email = request.session.get("otp_email")

        if not email:
            return redirect("login")

        stored_otp = cache.get(f"otp_{email}")

        if stored_otp and stored_otp == otp_input:
            user = User.objects.get(email=email)
            login(request, user)

            cache.delete(f"otp_{email}")
            del request.session['otp_email']

            return redirect("dashboard")

        return render(request, "dashboard/login.html", {
            "error": "Invalid OTP ❌",
            "otp_sent": True
        })

    return redirect("login")


# ========================= DASHBOARD ========================= #

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


# ========================= EXPENSE ========================= #

@login_required
def expense_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        category = request.POST.get("category")
        date_val = request.POST.get("date")

        expense = Expense.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            date=date_val
        )

        send_user_mail(
            request.user,
            "Expense Added 💸",
            f"You spent ₹{expense.amount} on {expense.title}"
        )

        return redirect("expenses")

    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    return render(request, "dashboard/expenses.html", {"expenses": expenses})


# ========================= INCOME ========================= #

@login_required
def income_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        category = request.POST.get("category")
        date_val = request.POST.get("date")

        Income.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            date=date_val
        )

        return redirect("income")

    incomes = Income.objects.filter(user=request.user).order_by('-date')

    return render(request, "dashboard/income.html", {"incomes": incomes})


# ========================= REPORT ========================= #

@login_required
def reports(request):
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0

    if request.method == "POST":
        message = f"""
Income: ₹{total_income}
Expense: ₹{total_expense}
"""
        send_user_mail(request.user, "Your Report 📊", message)
        messages.success(request, "Report sent successfully")

    return render(request, "dashboard/reports.html")