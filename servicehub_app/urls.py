from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('api/nearby-providers/', views.find_nearby_providers, name='nearby_providers'),
    path('api/book/<int:provider_id>/', views.create_booking, name='create_booking'),
    path('api/my-bookings/', views.get_my_bookings, name='my_bookings'),
    path('dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('apply/', views.apply_provider, name='apply_provider'), # New custom form path
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='servicehub_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/client/', views.register_client, name='register_client'),
    path('register/provider/', views.apply_provider, name='apply_provider'),
    path('api/book/<int:provider_id>/', views.create_booking, name='create_booking'),
    path('my-history/', views.client_history_view, name='client_history'),
    path('api/complete-job/<int:booking_id>/', views.complete_job, name='complete_job'),
    path('api/submit-rating/', views.submit_rating, name='submit_rating'),
    path('api/send-quote/<int:booking_id>/', views.send_quote, name='send_quote'),
    path('api/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('contact/', views.contact_page, name='contact'),
    path('api/service-suggestions/', views.service_suggestions, name='service_suggestions'),


]