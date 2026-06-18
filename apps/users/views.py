from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework              import status
from rest_framework.response     import Response
from rest_framework.views        import APIView
from rest_framework.permissions  import AllowAny , IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils                import timezone
from .serializers                import RegisterSerializer, UserSerializer, LoginSerializer , ProfileSerializer , ChangePasswordSerializer
from .models                     import UserStatus, User   # ← User added here, needed by the new views below

class RegisterView(APIView):
    # AllowAny → anyone can access this endpoint
    # overrides our default IsAuthenticated in settings.py
    permission_classes = [AllowAny]

    def post(self, request):
        # pass incoming request data to serializer
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            # validation passed → create user
            user = serializer.save()

            # ── NEW — send verification email right after registration ──
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            verify_link = f'{settings.FRONTEND_URL}/verify-email/{uid}/{token}/'

            send_mail(
                subject='Verify your email',
                message=f'Click to verify your email: {verify_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
            # ── END NEW ──

            # return created user data using UserSerializer
            # we use UserSerializer not RegisterSerializer
            # because RegisterSerializer has passwords in it
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED  # 201 = Created successfully
            )

        # validation failed → return errors
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST  # 400 = Bad request
        )
    
class LoginView(APIView):
    permission_classes = [AllowAny]  # anyone can login

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # generate JWT tokens for this user
            refresh = RefreshToken.for_user(user)

            # update user status to online + last seen
            # user.status    = UserStatus.ONLINE
            user.last_seen = timezone.now()
            user.save()

            return Response({
                'user'   : UserSerializer(user).data,
                'tokens' : {
                    'access' : str(refresh.access_token), # short lived token
                    'refresh': str(refresh),              # long lived token
                }
            }, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ProfileView(APIView):
    permission_classes = [IsAuthenticated] # must be logged in

    def get(self, request):
        # request.user → automatically set by JWT authentication
        # contains the logged in user object
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # partial=True → allow updating only some fields
        # without partial → ALL fields become required
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # get refresh token from request body
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # blacklist the token → cannot be used again
            token = RefreshToken(refresh_token)
            token.blacklist()

            # update user status to offline
            # request.user.status = UserStatus.OFFLINE
            # request.user.save()

            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # pass request in context so serializer can access logged in user
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully.'},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ── NEW — Email Verification ──────────────────────────
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Verification link is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_email_verified = True
        user.save()
        return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)


# ── NEW — Forgot Password ──────────────────────────────
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # same response whether or not the email exists
        # WHY → prevents this endpoint being used to discover registered emails
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f'{settings.FRONTEND_URL}/reset-password/{uid}/{token}/'

            send_mail(
                subject='Reset your password',
                message=f'Click to reset your password: {reset_link}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

        return Response(
            {'message': 'If that email exists, a reset link has been sent.'},
            status=status.HTTP_200_OK
        )


# ── NEW — Reset Password ────────────────────────────────
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Reset link is invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not new_password or new_password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)


# ── NEW — Deactivate Account ────────────────────────────
class DeactivateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # require current password — prevents a stolen session from
        # deactivating the account without proving the password is known
        password = request.data.get('password')
        if not password or not request.user.check_password(password):
            return Response({'error': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.is_active = False
        request.user.save()
        return Response(
            {'message': 'Account deactivated. You have been logged out.'},
            status=status.HTTP_200_OK
        )