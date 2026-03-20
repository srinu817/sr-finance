from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.conf import settings
from django.core.mail import send_mail
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
def send_user_mail(user, subject, message):
    if not user.email:
        print("❌ No email")
        return

    try:
        url = "https://api.sendgrid.com/v3/mail/send"

        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "personalizations": [
                {
                    "to": [{"email": user.email}],
                    "subject": subject
                }
            ],
            "from": {"email": settings.DEFAULT_FROM_EMAIL},
            "content": [
                {
                    "type": "text/plain",
                    "value": message
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)

        print("📩 STATUS:", response.status_code)
        print("📩 RESPONSE:", response.text)
        print("FROM:", settings.DEFAULT_FROM_EMAIL)

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
                "error": "Too many attempts. Try after 5 minutes ❌"
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

        otp_attempts = cache.get(f"otp_attempts_{email}", 0)
        if otp_attempts >= 3:
            return render(request, "dashboard/login.html", {
                "error": "Too many OTP requests. Try later ❌"
            })

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "dashboard/login.html", {"error": "User not found"})

        otp = str(random.randint(100000, 999999))

        cache.set(f"otp_{email}", otp, timeout=300)
        cache.set(f"otp_timer_{email}", True, timeout=30)
        cache.set(f"otp_attempts_{email}", otp_attempts + 1, timeout=300)

        request.session['otp_email'] = email

        send_user_mail(user, "Your OTP", f"OTP: {otp}")

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
            cache.delete(f"otp_attempts_{email}")

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

    cache_key = f"dashboard_{request.user.id}"
    data = cache.get(cache_key)

    if not data:
        total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
        total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
        total_loan = Loan.objects.filter(user=request.user).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        wallet = total_income - total_expense - total_loan

        data = {
            "total_income": total_income,
            "total_expense": total_expense,
            "total_loan": total_loan,
            "wallet": wallet
        }

        cache.set(cache_key, data, timeout=60)

    return render(request, "dashboard/dashboard.html", data)


# ========================= EXPENSE ========================= #

# ========================= EXPENSE ========================= #

from django.db.models import Sum
from datetime import datetime

@login_required
def expense_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        category = request.POST.get("category")
        date_val = request.POST.get("date")

        if not title or not amount:
            return redirect("expenses")

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

        cache.delete(f"dashboard_{request.user.id}")

        return redirect("expenses")

    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    # ✅ Monthly total
    current_month = datetime.now().month
    current_year = datetime.now().year

    total_expense = Expense.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, "dashboard/expenses.html", {
        "expenses": expenses,
        "total_expense": total_expense
    })


@login_required
def delete_expense(request, id):
    exp = get_object_or_404(Expense, id=id, user=request.user)
    exp.delete()

    cache.delete(f"dashboard_{request.user.id}")

    return redirect("expenses")


# ========================= INCOME ========================= #

# ========================= INCOME ========================= #

# from django.db.models import Sum
# from datetime import datetime

# @login_required
# def income_view(request):
#     if request.method == "POST":
#      title = request.POST.get("title")
#     amount = request.POST.get("amount")
#     category = request.POST.get("category")
#     date_val = request.POST.get("date")

#     if not title or not amount:
#         return redirect("income")

#     income = Income.objects.create(
#         user=request.user,
#         title=title,
#         amount=amount,
#         category=category,
#         date=date_val
#     )

#     send_user_mail(
#         request.user,
#         "Income Added 💰",
#         f"You received ₹{income.amount} from {income.title}"
#     )

#     cache.delete(f"dashboard_{request.user.id}")

#     return redirect("income")

        

#     # ✅ Get all incomes (latest first)
#     incomes = Income.objects.filter(user=request.user).order_by('-date')

#     # ✅ Monthly total calculation
#     current_month = datetime.now().month
#     current_year = datetime.now().year

#     total_income = Income.objects.filter(
#         user=request.user,
#         date__month=current_month,
#         date__year=current_year
#     ).aggregate(total=Sum('amount'))['total'] or 0

#     return render(request, "dashboard/income.html", {
#         "incomes": incomes,
#         "total_income": total_income
#     })


@login_required
def delete_income(request, id):
    inc = get_object_or_404(Income, id=id, user=request.user)
    inc.delete()

    cache.delete(f"dashboard_{request.user.id}")

    return redirect("income")
@login_required
def income_view(request):

    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        category = request.POST.get("category")
        date_val = request.POST.get("date")

        if not title or not amount:
            return redirect("income")

        Income.objects.create(
            user=request.user,
            title=title,
            amount=amount,
            category=category,
            date=date_val
        )

        cache.delete(f"dashboard_{request.user.id}")
        return redirect("income")

    # ✅ GET request (NO title usage here)
    incomes = Income.objects.filter(user=request.user).order_by('-date')

    from django.db.models import Sum
    from datetime import datetime

    current_month = datetime.now().month
    current_year = datetime.now().year

    total_income = Income.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, "dashboard/income.html", {
        "incomes": incomes,
        "total_income": total_income
    })

# ========================= LOANS ========================= #

# ========================= LOANS ========================= #

from django.db.models import Sum

@login_required
def loans_view(request):
    loans = Loan.objects.filter(user=request.user)

    total_debt = Loan.objects.filter(
        user=request.user,
        status="Active"
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    return render(request, "dashboard/loans.html", {
        "loans": loans,
        "total_debt": total_debt
    })


@login_required
def add_loan(request):
    if request.method == "POST":
        person = request.POST.get("person")
        total_amount = request.POST.get("total_amount")
        date = request.POST.get("date")

        Loan.objects.create(
            user=request.user,
            person=person,
            total_amount=total_amount,
            date=date
        )

        cache.delete(f"dashboard_{request.user.id}")
        return redirect("loans")

    return render(request, "dashboard/add_loan.html")


@login_required
def delete_loan(request, id):
    loan = get_object_or_404(Loan, id=id, user=request.user)
    loan.delete()

    cache.delete(f"dashboard_{request.user.id}")

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