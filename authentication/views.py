"""
Authentication views for SSO and user management.
"""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid
from urllib.parse import urlencode, urlparse

from .forms import (
    EmailAuthenticationForm, CompanyUserCreationForm, UserProfileForm,
    UserRegistrationForm, UserPasswordChangeForm
)
from .models import CompanyUser, UserSession, ApplicationConfig


class EmailLoginView(LoginView):
    """
    Custom login view using email authentication.
    """
    form_class = EmailAuthenticationForm
    template_name = 'authentication/login.html'
    success_url = reverse_lazy('dashboard:home')

    def form_invalid(self, form):
        """Check if login failed due to pending approval."""
        email = form.data.get('username', '').lower()
        if email:
            # Check if user exists but is not approved
            try:
                user = CompanyUser.objects.get(email=email)
                if not user.is_approved:
                    messages.error(
                        self.request,
                        _('Your account is pending approval by an administrator. '
                          'Please wait for approval notification.')
                    )
                elif not user.is_active:
                    messages.error(
                        self.request,
                        _('Your account has been deactivated. '
                          'Please contact your administrator.')
                    )
            except CompanyUser.DoesNotExist:
                pass  # Let default error message show

        return super().form_invalid(form)

    def form_valid(self, form):
        """Login user and update SSO token."""
        response = super().form_valid(form)

        # Update last SSO login time
        user = self.request.user
        user.last_sso_login = timezone.now()
        user.save(update_fields=['last_sso_login'])

        messages.success(
            self.request,
            _('Welcome back, {}!').format(user.get_display_name())
        )

        # Handle SSO app redirects
        return_to = self.request.GET.get('return_to')
        app_name = self.request.GET.get('app')

        if return_to and app_name:
            # Check if user has access to the app
            if user.has_app_access(app_name):
                # Generate return URL with SSO token
                return_url = f"{return_to}?sso_token={user.sso_token}"
                return HttpResponseRedirect(return_url)
            else:
                messages.error(
                    self.request,
                    _('You do not have access to the requested application.')
                )

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Company Platform Login')
        return context


class EmailLogoutView(LogoutView):
    """
    Custom logout view that cleans up SSO sessions.
    """
    next_page = reverse_lazy('authentication:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Clean up user's SSO sessions
            UserSession.objects.filter(user=request.user).delete()
            messages.info(
                request,
                _('You have been logged out from all applications.')
            )
        return super().dispatch(request, *args, **kwargs)


class UserRegistrationView(CreateView):
    """
    Simplified self-registration view for internal staff.
    Creates user with is_approved=False, requiring superadmin approval.
    """
    model = CompanyUser
    form_class = UserRegistrationForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('authentication:registration_pending')

    def form_valid(self, form):
        """Create user pending approval and show success message."""
        response = super().form_valid(form)
        user = form.instance
        messages.success(
            self.request,
            _('Registration submitted successfully! Your account is pending approval by an administrator. '
              'You will receive notification once your account is approved.')
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Register for Company Platform')
        return context


def registration_pending(request):
    """View shown after successful registration while awaiting approval."""
    return render(request, 'authentication/registration_pending.html', {
        'page_title': _('Registration Pending Approval')
    })


@method_decorator(login_required, name='dispatch')
class UserProfileView(UpdateView):
    """
    View for updating user profile.
    """
    model = CompanyUser
    form_class = UserProfileForm
    template_name = 'authentication/profile.html'
    success_url = reverse_lazy('authentication:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        """Update profile and show success message."""
        response = super().form_valid(form)
        messages.success(
            self.request,
            _('Profile updated successfully.')
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('My Profile')
        context['user_sessions'] = UserSession.objects.filter(
            user=self.request.user
        ).order_by('-last_activity')[:10]
        return context


# SSO API Views

@csrf_exempt
@require_http_methods(["GET", "POST"])
def sso_validate_token(request):
    """
    API endpoint to validate SSO tokens from other applications.
    """
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            token = request.GET.get('token')
            app_name = request.GET.get('app_name', 'unknown')
        else:
            data = json.loads(request.body)
            token = data.get('token')
            app_name = data.get('app_name', 'unknown')

        if not token:
            return JsonResponse({
                'valid': False,
                'error': 'Token is required'
            }, status=400)

        # Find user by SSO token
        try:
            user = CompanyUser.objects.get(
                sso_token=token,
                is_active=True
            )
        except CompanyUser.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'error': 'Invalid token'
            }, status=401)

        # Check if user has access to the application
        if not user.has_app_access(app_name) and not user.is_superuser:
            return JsonResponse({
                'valid': False,
                'error': 'Access denied to application'
            }, status=403)

        # Create or update session
        session_key = str(uuid.uuid4())
        expires_at = timezone.now() + timezone.timedelta(hours=8)

        session, created = UserSession.objects.update_or_create(
            user=user,
            app_name=app_name,
            defaults={
                'session_key': session_key,
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'expires_at': expires_at,
            }
        )

        return JsonResponse({
            'valid': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name(),
                'employee_id': user.employee_id,
                'region': user.region,
                'department': user.department,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
            'session_key': session_key,
            'expires_at': expires_at.isoformat(),
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'valid': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'valid': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def sso_get_user_info(request):
    """
    API endpoint to get user information by token.
    """
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            token = request.GET.get('token')
        else:
            data = json.loads(request.body)
            token = data.get('token')

        if not token:
            return JsonResponse({
                'error': 'Token is required'
            }, status=400)

        # Find user by SSO token
        try:
            user = CompanyUser.objects.get(
                sso_token=token,
                is_active=True
            )
        except CompanyUser.DoesNotExist:
            return JsonResponse({
                'error': 'Invalid token'
            }, status=401)

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'employee_id': user.employee_id,
            'region': user.region,
            'department': user.department,
            'phone': user.phone,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'apps_access': user.apps_access,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def sso_logout(request):
    """
    API endpoint to logout from SSO session.
    """
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')

        if not session_key:
            return JsonResponse({
                'error': 'Session key is required'
            }, status=400)

        # Delete session
        deleted_count, _ = UserSession.objects.filter(
            session_key=session_key
        ).delete()

        return JsonResponse({
            'success': True,
            'message': 'Logged out successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
def refresh_sso_token(request):
    """
    View to refresh user's SSO token.
    """
    user = request.user
    old_token = user.sso_token
    new_token = user.refresh_sso_token()

    # Invalidate all existing sessions
    UserSession.objects.filter(user=user).delete()

    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'success': True,
            'new_token': str(new_token),
            'message': 'SSO token refreshed successfully'
        })
    else:
        messages.success(
            request,
            _('SSO token refreshed successfully. Please re-login to other applications.')
        )
        return redirect('authentication:profile')


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def change_password(request):
    """View for users to change their password."""
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(
                request,
                _('Password changed successfully.')
            )
            return redirect('authentication:profile')
    else:
        form = UserPasswordChangeForm(request.user)

    return render(request, 'authentication/change_password.html', {
        'form': form,
        'page_title': _('Change Password')
    })


@login_required
def pending_approvals(request):
    """View for superadmin to see and manage pending user registrations."""
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard:home')

    # Get all pending registrations
    pending_users = CompanyUser.objects.filter(
        is_approved=False,
        is_active=False
    ).order_by('-date_joined')

    return render(request, 'authentication/pending_approvals.html', {
        'pending_users': pending_users,
        'page_title': _('Pending User Approvals')
    })


@login_required
def approve_user(request, user_id):
    """Approve a pending user registration."""
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to perform this action.'))
        return redirect('dashboard:home')

    try:
        user = CompanyUser.objects.get(id=user_id, is_approved=False)
        user.is_approved = True
        user.is_active = True
        user.approved_by = request.user
        user.approved_at = timezone.now()
        user.save()

        messages.success(
            request,
            _('User {} ({}) has been approved and can now login.').format(
                user.get_full_name(),
                user.email
            )
        )
    except CompanyUser.DoesNotExist:
        messages.error(request, _('User not found or already approved.'))

    return redirect('authentication:pending_approvals')


@login_required
def reject_user(request, user_id):
    """Reject and delete a pending user registration."""
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to perform this action.'))
        return redirect('dashboard:home')

    try:
        user = CompanyUser.objects.get(id=user_id, is_approved=False)
        user_email = user.email
        user_name = user.get_full_name()
        user.delete()

        messages.success(
            request,
            _('Registration for {} ({}) has been rejected and deleted.').format(
                user_name,
                user_email
            )
        )
    except CompanyUser.DoesNotExist:
        messages.error(request, _('User not found or already approved.'))

    return redirect('authentication:pending_approvals')
