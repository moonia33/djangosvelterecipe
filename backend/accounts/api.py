"""Autentifikacijos susiję API maršrutai."""

from ninja import Router
from ninja.errors import HttpError

from notifications.forms import TemplatedPasswordResetForm

from .schemas import PasswordResetRequestSchema, PasswordResetResponseSchema

router = Router(tags=["Auth"])


@router.post("/password-reset", response=PasswordResetResponseSchema)
def request_password_reset(request, payload: PasswordResetRequestSchema):
    """Priima el. paštą ir išsiunčia slaptažodžio atkūrimo laišką."""

    form = TemplatedPasswordResetForm(data={"email": payload.email})
    if not form.is_valid():
        raise HttpError(422, "Neteisingas el. pašto adresas")

    form.save(request=request, use_https=request.is_secure())
    return PasswordResetResponseSchema(sent=True)
