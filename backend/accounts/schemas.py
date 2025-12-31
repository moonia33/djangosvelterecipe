"""Schemos autentifikacijos veiksmams."""

from ninja import Field, Schema


class PasswordResetRequestSchema(Schema):
    email: str = Field(..., description="Naudotojo el. pašto adresas")


class PasswordResetResponseSchema(Schema):
    sent: bool = True
