from django.contrib import admin
from .models import UserProfile, Booking, Provider, Client, ClientFeedback, ProviderFeedback
from django.utils import timezone
from django.db.models import Sum


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_type', 'is_provider', 'is_verified')
    list_filter = ('is_provider', 'is_verified', 'service_type')
    search_fields = ('user__username', 'service_type')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'provider', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')

    def changelist_view(self, request, extra_context=None):
        # Get the current filtered results
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        # 1. Gross Summation (Total Fees)
        gross_total = qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # 2. Platform Retention (10%)
        platform_retention = float(gross_total) * 0.10

        # 3. Provider Share (90%)
        provider_share = float(gross_total) * 0.90

        # Pass these values to the default admin template
        extra_info = {
            'total_revenue': gross_total,
            'net_retention': platform_retention,
            'provider_payouts': provider_share,
        }

        response.context_data.update(extra_info)
        return response

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    # Only show users marked as providers
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_provider=True)

    list_display = ('user', 'service_type', 'is_verified', 'phone_number', 'latitude', 'longitude')
    list_filter = ('is_verified', 'service_type')
    search_fields = ('user__username', 'service_type')

    # Action for manual verification per your project methodology
    actions = ['make_verified']

    @admin.action(description='Verify selected providers')
    def make_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "Providers verified for 3km radius matching.")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Only show users NOT marked as providers
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_provider=False)

    list_display = ('user', 'phone_number')
    search_fields = ('user__username',)


@admin.register(ClientFeedback)
class ClientFeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('subject', 'message', 'user__username')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='client')


@admin.register(ProviderFeedback)
class ProviderFeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('subject', 'message', 'user__username')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type='provider')