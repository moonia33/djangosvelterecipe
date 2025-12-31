"""Autentifikacijos susiję API maršrutai."""

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from ninja import Router
from ninja.errors import HttpError

from notifications.forms import TemplatedPasswordResetForm

from .schemas import (
    LoginRequestSchema,
    PasswordResetRequestSchema,
    PasswordResetResponseSchema,
    SessionSchema,
    UserPublicSchema,
)

router = Router(tags=["Auth"])
User = get_user_model()


def _serialize_user(user) -> UserPublicSchema:
    return UserPublicSchema(
        id=user.id,
        email=user.email or "",
        username=user.get_username(),
        full_name=user.get_full_name() or None,
    )


def _authenticate_credentials(request, identifier: str, password: str):
    identity = (identifier or "").strip()
    user = authenticate(request, username=identity, password=password)
    if user:
        return user
    if "@" in identity:
        try:
            user_obj = User.objects.get(email__iexact=identity)
        except User.DoesNotExist:
            return None
        return authenticate(request, username=user_obj.get_username(), password=password)
    return None


def _session_payload(request, user=None) -> SessionSchema:
    current_user = user or (request.user if request.user.is_authenticated else None)
    return SessionSchema(
        is_authenticated=current_user is not None,
        csrf_token=get_token(request),
        user=_serialize_user(current_user) if current_user else None,
    )


@router.get("/session", response=SessionSchema)
@ensure_csrf_cookie
def get_session(request):
    """Grąžina naudotojo sesijos būseną ir atnaujina CSRF slapuką."""

    return _session_payload(request)


@router.post("/login", response=SessionSchema)
@csrf_protect
def login_user(request, payload: LoginRequestSchema):
    """Autentikuoja naudotoją ir sukuria sesiją."""

    user = _authenticate_credentials(request, payload.identifier, payload.password)
    if not user:
        raise HttpError(401, "Neteisingi prisijungimo duomenys")
    if not user.is_active:
        raise HttpError(403, "Paskyra neaktyvi")

    login(request, user)
    return _session_payload(request, user)


@router.post("/logout", response=SessionSchema)
@csrf_protect
def logout_user(request):
    """Atsijungia ir sukuria naują CSRF tokeną naujam seansui."""

    logout(request)
    return _session_payload(request)


@router.post("/password-reset", response=PasswordResetResponseSchema)
@csrf_protect
def request_password_reset(request, payload: PasswordResetRequestSchema):
    """Priima el. paštą ir išsiunčia slaptažodžio atkūrimo laišką."""

    form = TemplatedPasswordResetForm(data={"email": payload.email})
    if not form.is_valid():
        raise HttpError(422, "Neteisingas el. pašto adresas")

    form.save(request=request, use_https=request.is_secure())
    return PasswordResetResponseSchema(sent=True)
