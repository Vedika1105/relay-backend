from django.urls import path
from .views import RegisterView , LoginView , ProfileView , LogoutView , ChangePasswordView , VerifyEmailView , ForgotPasswordView , ResetPasswordView , DeactivateAccountView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('profile/', ProfileView.as_view(), name='user-profile'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-passowrd'),
    path('verify-email/<str:uidb64>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<str:uidb64>/<str:token>/', ResetPasswordView.as_view(), name='reset-password'),
    path('deactivate/', DeactivateAccountView.as_view(), name='deactivate-account'),
]