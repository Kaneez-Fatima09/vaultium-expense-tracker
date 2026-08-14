from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import send_mail
from django.conf import settings
from .models import Expense, Category, FeedbackSupport, Wallet, PersonalVault, UserVaultProfile
from .forms import ExpenseForm, FeedbackForm
from datetime import date
import json
import calendar

def ensure_default_categories():
    defaults = ['Food & Dining', 'Shopping', 'Bills & Utilities', 'Entertainment', 'Investments', 'Transport', 'General']
    for cat_name in defaults:
        Category.objects.get_or_create(name=cat_name)

def home_landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'expenses/landing.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Wallet.objects.create(user=user, name="Main Wallet", balance=0.00, is_default=True)
            UserVaultProfile.objects.create(user=user)
            messages.success(request, "Registration successful! Please login to continue.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'expenses/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            
    return render(request, 'expenses/login.html')

def logout_view(request):
    logout(request)
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']

    ensure_default_categories()
    
    wallets = Wallet.objects.filter(user=request.user)
    if not wallets.exists():
        Wallet.objects.create(user=request.user, name="Main Wallet", balance=0.00, is_default=True)
        wallets = Wallet.objects.filter(user=request.user)

    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    
    query = request.GET.get('q')
    if query:
        expenses = expenses.filter(title__icontains=query)

    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00
    
    category_data = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else "General"
        category_data[cat_name] = category_data.get(cat_name, 0) + float(exp.amount)

    context = {
        'expenses': expenses[:10],
        'total_spent': total_spent,
        'wallets': wallets,
        'cat_labels': json.dumps(list(category_data.keys())),
        'cat_values': json.dumps(list(category_data.values())),
    }
    return render(request, 'expenses/dashboard.html', context)

@login_required(login_url='login')
def add_wallet(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    if request.method == 'POST':
        name = request.POST.get('name')
        account_type = request.POST.get('account_type', 'savings')
        balance = request.POST.get('balance', 0.00)

        if name:
            Wallet.objects.create(user=request.user, name=name, account_type=account_type, balance=balance)
            messages.success(request, f"Bank Account '{name}' added successfully!")
    return redirect('dashboard')

@login_required(login_url='login')
def delete_wallet(request, pk):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
    if request.method == 'POST':
        wallet_name = wallet.name
        wallet.delete()
        messages.success(request, f"Bank Account '{wallet_name}' deleted successfully!")
    return redirect('dashboard')

@login_required(login_url='login')
def yearly_history_view(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    today = date.today()
    current_year = today.year
    expenses_year = Expense.objects.filter(user=request.user, date__year=current_year)

    monthly_summary = []
    month_names = []
    month_spendings = []

    for m in range(1, 13):
        m_name = calendar.month_name[m]
        total_m = expenses_year.filter(date__month=m).aggregate(Sum('amount'))['amount__sum'] or 0.0
        total_m_float = float(total_m)

        monthly_summary.append({'month': m_name, 'amount': total_m_float})
        month_names.append(m_name)
        month_spendings.append(total_m_float)

    yearly_total = sum(item['amount'] for item in monthly_summary)

    context = {
        'current_year': current_year,
        'monthly_summary': monthly_summary,
        'yearly_total': yearly_total,
        'month_names_json': json.dumps(month_names),
        'month_spendings_json': json.dumps(month_spendings)
    }
    return render(request, 'expenses/yearly_history.html', context)

@login_required(login_url='login')
def analytics_view(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    expenses = Expense.objects.filter(user=request.user)
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00
    
    category_data = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else "General"
        category_data[cat_name] = category_data.get(cat_name, 0) + float(exp.amount)

    context = {
        'total_spent': total_spent,
        'cat_labels': json.dumps(list(category_data.keys())),
        'cat_values': json.dumps(list(category_data.values())),
    }
    return render(request, 'expenses/analytics.html', context)

@login_required(login_url='login')
def budgets_view(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    ensure_default_categories()
    expenses = Expense.objects.filter(user=request.user)
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0.00
    categories = Category.objects.all()
    budget_list = []
    
    for cat in categories:
        cat_spent = expenses.filter(category=cat).aggregate(Sum('amount'))['amount__sum'] or 0.00
        target = 10000.00
        percentage = min(int((float(cat_spent) / target) * 100), 100) if target > 0 else 0
        
        budget_list.append({'category': cat.name, 'spent': cat_spent, 'target': target, 'percentage': percentage})

    return render(request, 'expenses/budgets.html', {'total_spent': total_spent, 'budgets': budget_list})

@login_required(login_url='login')
def add_expense(request):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    ensure_default_categories()
    today = date.today()
    min_date = date(today.year, today.month, 1).strftime('%Y-%m-%d')
    max_date = today.strftime('%Y-%m-%d')
    wallets = Wallet.objects.filter(user=request.user)

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            
            wallet_id = request.POST.get('wallet')
            if wallet_id:
                wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user)
                expense.wallet = wallet
                wallet.balance -= expense.amount
                wallet.save()

            expense.save()
            messages.success(request, "Expense added successfully!")
            return redirect('dashboard')
    else:
        form = ExpenseForm()

    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Add New Transaction', 'wallets': wallets, 'min_date': min_date, 'max_date': max_date})

@login_required(login_url='login')
def edit_expense(request, pk):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    old_amount = expense.amount
    old_wallet = expense.wallet

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            updated_expense = form.save(commit=False)
            wallet_id = request.POST.get('wallet')
            new_wallet = get_object_or_404(Wallet, id=wallet_id, user=request.user) if wallet_id else None

            if old_wallet:
                old_wallet.balance += old_amount
                old_wallet.save()

            if new_wallet:
                new_wallet.balance -= updated_expense.amount
                new_wallet.save()
                updated_expense.wallet = new_wallet

            updated_expense.save()
            messages.success(request, "Expense updated successfully!")
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)

    wallets = Wallet.objects.filter(user=request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Edit Transaction', 'wallets': wallets})

@login_required(login_url='login')
def delete_expense(request, pk):
    if 'vault_unlocked' in request.session:
        del request.session['vault_unlocked']
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        if expense.wallet:
            expense.wallet.balance += expense.amount
            expense.wallet.save()
        expense.delete()
        messages.success(request, "Transaction removed successfully.")
        return redirect('dashboard')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})


# ==========================================
# Personal Vault & PIN Security Views
# ==========================================

@login_required(login_url='login')
def vault_unlock_view(request):
    profile, created = UserVaultProfile.objects.get_or_create(user=request.user)
    
    if not profile.vault_pin:
        return redirect('vault_setup')

    if request.method == 'POST':
        entered_pin = request.POST.get('pin')
        if entered_pin == profile.vault_pin:
            request.session['vault_unlocked'] = True
            return redirect('vault_list')
        else:
            messages.error(request, "Incorrect Vault PIN!")
            
    return render(request, 'expenses/vault_unlock.html')

@login_required(login_url='login')
def vault_setup_view(request):
    profile, created = UserVaultProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        new_pin = request.POST.get('pin')
        confirm_pin = request.POST.get('confirm_pin')
        question = request.POST.get('security_question')
        answer = request.POST.get('security_answer')

        if new_pin != confirm_pin:
            messages.error(request, "New PINs do not match!")
        elif len(new_pin) < 4:
            messages.error(request, "PIN must be at least 4 digits long.")
        else:
            profile.vault_pin = new_pin
            profile.security_question = question
            profile.security_answer = answer.strip().lower() if answer else ""
            profile.save()
            messages.success(request, "Vault PIN created successfully! Now unlock your vault.")
            return redirect('vault_unlock')

    return render(request, 'expenses/vault_setup.html', {'has_pin': bool(profile.vault_pin)})

@login_required(login_url='login')
def vault_forgot_view(request):
    profile, created = UserVaultProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        answer = request.POST.get('security_answer', '').strip().lower()
        new_pin = request.POST.get('new_pin')

        if answer == profile.security_answer:
            profile.vault_pin = new_pin
            profile.save()
            messages.success(request, "PIN reset successfully! Please login with your new PIN.")
            return redirect('vault_unlock')
        else:
            messages.error(request, "Incorrect security answer!")

    return render(request, 'expenses/vault_forgot.html', {'question': profile.security_question})

@login_required(login_url='login')
def vault_list_view(request):
    if not request.session.get('vault_unlocked', False):
        return redirect('vault_unlock')
        
    vault_items = PersonalVault.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'expenses/vault_list.html', {'vault_items': vault_items})

@login_required(login_url='login')
def add_vault_item(request):
    if not request.session.get('vault_unlocked', False):
        return redirect('vault_unlock')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        if title:
            PersonalVault.objects.create(user=request.user, title=title, content=content, file=file)
            messages.success(request, "Secure item/file added to your Personal Vault successfully!")
    return redirect('vault_list')

@login_required(login_url='login')
def delete_vault_item(request, pk):
    if not request.session.get('vault_unlocked', False):
        return redirect('vault_unlock')
        
    vault_item = get_object_or_404(PersonalVault, pk=pk, user=request.user)
    if request.method == 'POST':
        vault_item.delete()
        messages.success(request, "Vault item removed successfully.")
    return redirect('vault_list')

def help_view(request):
    return render(request, 'expenses/help.html')

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()

            subject_line = f"[Vaultium Support] {feedback.subject}"
            email_body = f"From: {feedback.name} ({feedback.email})\n\nMessage:\n{feedback.message}"

            try:
                send_mail(subject_line, email_body, settings.DEFAULT_FROM_EMAIL, ['89kaneezfatima@gmail.com'], fail_silently=False)
            except Exception as e:
                print("Email sending error:", e)

            messages.success(request, "Thank you! Your feedback has been sent successfully.")
            return redirect('feedback')
    else:
        form = FeedbackForm()
        
    return render(request, 'expenses/feedback.html', {'form': form})

def privacy_policy_view(request):
    return render(request, 'expenses/privacy.html')