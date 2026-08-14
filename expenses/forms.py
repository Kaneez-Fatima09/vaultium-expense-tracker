from django import forms
from datetime import date
from .models import Expense, FeedbackSupport


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control custom-dark-input w-100',
                'placeholder': 'e.g. Grocery Shopping, Monthly Rent',
                'style': 'width: 100% !important;'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control custom-dark-input',
                'placeholder': '0.00'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select custom-dark-input'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control custom-dark-input'
            }),
        }

    def clean_date(self):
        selected_date = self.cleaned_data.get('date')
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)

        if selected_date and selected_date > today:
            raise forms.ValidationError("Future dates are not allowed! Expenses must be recorded on or before today.")
        if selected_date and selected_date < first_day_of_month:
            raise forms.ValidationError(f"Date must be within the current month ({today.strftime('%B %Y')}).")
            
        return selected_date


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackSupport
        fields = ['name', 'email', 'subject', 'message']