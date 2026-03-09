from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    # Link to the base Django User account
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Provider-Specific identification
    is_provider = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Professional Details
    service_type = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(upload_to='provider_photos/', null=True, blank=True)

    # Location for the 3km radius matching
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def get_rating(self):
        from django.db.models import Avg
        avg = Rating.objects.filter(provider=self.user).aggregate(Avg('stars'))['stars__avg']
        return round(avg, 1) if avg else 0

    def get_review_count(self):
        return Rating.objects.filter(provider=self.user).count()

    def __str__(self):
        return f"{self.user.username} - {'Provider' if self.is_provider else 'Client'}"


class Booking(models.Model):
    client = models.ForeignKey(User, related_name='bookings', on_delete=models.CASCADE)
    provider = models.ForeignKey(User, related_name='jobs', on_delete=models.CASCADE)
    description = models.TextField(help_text="Describe the issue or service needed")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    provider_cut = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    status = models.CharField(max_length=20, default='Pending')
    problem_photo = models.ImageField(upload_to='problem_photos/', null=True, blank=True)
    client_location_name = models.CharField(max_length=255, null=True, blank=True)

    is_paid_to_provider = models.BooleanField(default=False)
    payout_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.total_amount:
            self.provider_cut = float(self.total_amount) * 0.90
            self.platform_fee = float(self.total_amount) * 0.10
        super().save(*args, **kwargs)


class Provider(UserProfile):
    class Meta:
        proxy = True
        verbose_name = "Service Provider"
        verbose_name_plural = "Service Providers"


class Client(UserProfile):
    class Meta:
        proxy = True
        verbose_name = "Client"
        verbose_name_plural = "Clients"


class Rating(models.Model):
    provider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    stars = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'client')


class Feedback(models.Model):
    USER_TYPES = (
        ('client', 'Client'),
        ('provider', 'Provider'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, verbose_name="Mark as Addressed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "All Feedback"

    def __str__(self):
        return f"{self.subject} - {self.user.username}"


# Proxy Models for Jazmin sidebar separation
class ClientFeedback(Feedback):
    class Meta:
        proxy = True
        verbose_name = "Client Feedback"
        verbose_name_plural = "Client Feedback"


class ProviderFeedback(Feedback):
    class Meta:
        proxy = True
        verbose_name = "Provider Feedback"
        verbose_name_plural = "Provider Feedback"

