from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from math import radians, cos, sin, asin, sqrt
from django.shortcuts import get_object_or_404, redirect
from .models import Booking, UserProfile, Rating, Feedback
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import json
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.views import LoginView
from django.contrib import messages


# Haversine formula to calculate distance in km
def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius
    return c * r


# 1. View to render the HTML home page
def home(request):
    return render(request, 'servicehub_app/index.html')


# 2. API View to return nearby providers as JSON

# 2. API View to return nearby providers as JSON
def find_nearby_providers(request):
    client_lat = request.GET.get('lat')
    client_lon = request.GET.get('lon')
    service_query = request.GET.get('service')

    if not client_lat or not client_lon:
        return JsonResponse({'error': 'Coordinates required'}, status=400)

    providers = UserProfile.objects.filter(is_provider=True, is_verified=True)

    if service_query:
        providers = providers.filter(service_type__icontains=service_query)

    nearby_list = []
    for p in providers:
        if p.latitude and p.longitude:
            dist = calculate_distance(client_lat, client_lon, p.latitude, p.longitude)
            if dist <= 3.0:
                nearby_list.append({
                    'id': p.id,
                    'name': p.user.get_full_name() or p.user.username,
                    'service': p.service_type,
                    'phone': p.phone_number,
                    'photo': p.profile_photo.url if p.profile_photo else None,
                    'distance_km': round(dist, 2),
                    'rating': p.get_rating(),
                    'review_count': p.get_review_count()
                })

    # MOVE THIS LINE TO THE LEFT (Outdent)
    return JsonResponse({'providers': nearby_list})
# 3. View to render the Registration page
def register_view(request):
    return render(request, 'servicehub_app/register.html')


def book_service(request, provider_id):
    if request.method == 'POST':
        provider_profile = get_object_or_404(UserProfile, id=provider_id)

        # Create the booking
        # For now, we use a fixed fee (e.g., 1000 KES) for testing
        Booking.objects.create(
            client=request.user,
            provider=provider_profile.user,
            total_amount=1000
        )
        return JsonResponse({'status': 'success', 'message': 'Booking request sent!'})

@csrf_protect
@login_required
def create_booking(request, provider_id):
    if request.method == 'POST':
        provider_profile = get_object_or_404(UserProfile, id=provider_id)
        provider_user = provider_profile.user

        # Get description from POST and photo from FILES
        location_name = request.POST.get('location_name')
        description = request.POST.get('description')
        photo = request.FILES.get('problem_photo')

        Booking.objects.create(
            client=request.user,
            provider=provider_user, # Now this links correctly
            description=description,
            problem_photo=photo,
            client_location_name=location_name,
            status='Pending'
        )
        return JsonResponse({'status': 'success', 'message': 'Booking request sent!'})

@login_required
def get_my_bookings(request):
    # Fetch bookings where the current user is the client
    bookings = Booking.objects.filter(client=request.user).order_by('-created_at')
    data = [{
        'provider': b.provider.username,
        'total_amount': b.total_amount,
        'status': b.status,
        'date': b.created_at.strftime("%Y-%m-%d")
    } for b in bookings]
    return JsonResponse(data, safe=False)


@login_required
def provider_dashboard(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    # All jobs for this provider
    all_jobs = Booking.objects.filter(provider=request.user).order_by('-created_at')

    # Filtered lists for the UI
    active_jobs = all_jobs.filter(is_paid_to_provider=False)
    payout_history = all_jobs.filter(is_paid_to_provider=True)

    # Financial Summaries
    total_earned = all_jobs.filter(status='completed').aggregate(Sum('provider_cut'))['provider_cut__sum'] or 0
    already_paid = payout_history.aggregate(Sum('provider_cut'))['provider_cut__sum'] or 0
    pending_payout = total_earned - already_paid

    context = {
        'active_jobs': active_jobs,
        'payout_history': payout_history,
        'total_earned': total_earned,
        'pending_payout': pending_payout,
        'already_paid': already_paid,
        'profile': profile
    }
    return render(request, 'servicehub_app/provider_dashboard.html', context)


def apply_provider(request):
    if request.method == 'POST':
        # Manually extracting data from the custom HTML form
        data = request.POST
        try:
            # 1. Create the User (Account Details)
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )

            # 2. Create the Profile (Professional Details)
            UserProfile.objects.create(
                user=user,
                is_provider=True,
                profile_photo=request.FILES.get('profile_photo'),
                service_type=data['service_type'],
                phone_number=data['phone_number'],
                bio=data['bio'],
                latitude=data['lat'],
                longitude=data['lon'],
                is_verified=False  # Requires admin oversight per methodology
            )

            messages.success(request, "Application submitted! Please wait for verification.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'servicehub_app/apply_provider.html')


def register_client(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, is_provider=False)
            login(request, user)
            # This message will be detected by our JavaScript on the next page
            messages.success(request, "Registration successful! You can now book services.")
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'servicehub_app/register_client.html', {'form': form})

@login_required
def client_history_view(request):
    return render(request, 'servicehub_app/client_history.html')


@login_required
def complete_job(request, booking_id):
    if request.method == 'POST':
        # Ensure the job belongs to the logged-in provider
        booking = get_object_or_404(Booking, id=booking_id, provider=request.user)

        if booking.status != 'completed':
            booking.status = 'completed'
            booking.save()
            return JsonResponse({'status': 'success', 'message': 'Job marked as completed!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@login_required
def submit_rating(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        provider_user = get_object_or_404(User, username=data['provider_username'])

        # Create or update the rating
        Rating.objects.update_or_create(
            client=request.user,
            provider=provider_user,
            defaults={'stars': data['stars'], 'comment': data.get('comment', '')}
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)



@login_required
def send_quote(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id, provider=request.user)
        data = json.loads(request.body)
        quote_price = data.get('price')

        if quote_price:
            booking.total_amount = quote_price
            # Change 'Quoted' to 'In Progress' so the Action button appears
            booking.status = 'In Progress'
            booking.save()

            return JsonResponse({'status': 'success', 'message': 'Quote sent! Job is now In Progress.'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def submit_feedback(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # Determine type based on UserProfile
        u_type = 'provider' if request.user.userprofile.is_provider else 'client'

        Feedback.objects.create(
            user=request.user,
            user_type=u_type,
            email=data['email'],
            subject=data['subject'],
            message=data['message']
        )
        return JsonResponse({'status': 'success', 'message': 'Thank you! Your feedback has been received.'})


def contact_page(request):
    return render(request, 'servicehub_app/contact.html')


def service_suggestions(request):
    query = request.GET.get('q', '')
    if len(query) < 2:  # Don't search for just one letter
        return JsonResponse([], safe=False)

    # Get distinct service types that match the query
    services = UserProfile.objects.filter(
        is_provider=True,
        is_verified=True,
        service_type__icontains=query
    ).values_list('service_type', flat=True).distinct()[:5]

    return JsonResponse(list(services), safe=False)

class MyLoginView(LoginView):
    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {self.request.user.username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)