from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_page'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('password-reset/', views.custom_password_reset, name='custom_password_reset'),

    # Django built-in password reset views
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('generate_curriculum/', views.generate_curriculum, name='generate_curriculum'),
    path('update_progress/', views.update_progress, name='update_progress'),
    path('curriculum/<int:curriculum_id>/progress/', views.get_curriculum_progress, name='get_curriculum_progress'),
    path('curriculum/<int:curriculum_id>/download/', views.download_curriculum_pdf, name='download_curriculum_pdf'),

    # Notes and Feedback
    path('add_note/', views.add_note, name='add_note'),
    path('get_notes/<int:curriculum_id>/<int:week_number>/', views.get_notes, name='get_notes'),
    path('add_feedback/', views.add_feedback, name='add_feedback'),

    # Admin Authentication URLs
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # Admin URLs (Protected)
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-curricula/', views.admin_curricula, name='admin_curricula'),
    path('admin-feedback/', views.admin_feedback, name='admin_feedback'),
    path('admin-toggle-user/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin-delete-user/', views.admin_delete_user, name='admin_delete_user'),
]
