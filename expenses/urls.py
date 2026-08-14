from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_landing, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-wallet/', views.add_wallet, name='add_wallet'),
    path('delete-wallet/<int:pk>/', views.delete_wallet, name='delete_wallet'),
    
    # Personal Vault Protected Routes & PIN Management
    path('vault/unlock/', views.vault_unlock_view, name='vault_unlock'),
    path('vault/setup/', views.vault_setup_view, name='vault_setup'),
    path('vault/forgot/', views.vault_forgot_view, name='vault_forgot'),
    path('vault/', views.vault_list_view, name='vault_list'),
    path('vault/add/', views.add_vault_item, name='add_vault_item'),
    path('vault/delete/<int:pk>/', views.delete_vault_item, name='delete_vault_item'),
    
    path('yearly-history/', views.yearly_history_view, name='yearly_history'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('budgets/', views.budgets_view, name='budgets'),
    
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    
    path('help/', views.help_view, name='help'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy'),
]