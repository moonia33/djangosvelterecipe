"""Schemos autentifikacijos veiksmams."""

from ninja import Field, Schema


class UserPublicSchema(Schema):
    id: int
    email: str
    username: str
    full_name: str | None = None


class SessionSchema(Schema):
    is_authenticated: bool
    csrf_token: str
    user: UserPublicSchema | None = None


class LoginRequestSchema(Schema):
    identifier: str = Field(..., description="Vartotojo vardas arba el. paštas")
    password: str = Field(..., description="Slaptažodis")


class PasswordResetRequestSchema(Schema):
    email: str = Field(..., description="Naudotojo el. pašto adresas")


class PasswordResetResponseSchema(Schema):
    sent: bool = True
