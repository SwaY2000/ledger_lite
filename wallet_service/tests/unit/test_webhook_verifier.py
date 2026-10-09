"""Webhook signature verification: valid, invalid, expired."""

import hashlib
import hmac

import pytest

from src.errors import InvalidSignatureError
from src.services.webhook_verifier import HmacWebhookSignatureVerifier


SECRET = 'secret'
NOW = 1_800_000_000
BODY = b'{"event_id":"evt_1","invoice_id":"inv_1","status":"paid","paid_amount":"10.00"}'


def _sign(body: bytes, timestamp: str, secret: str = SECRET) -> str:
    return 'sha256=' + hmac.new(secret.encode(), f'{timestamp}.'.encode() + body, hashlib.sha256).hexdigest()


@pytest.fixture
def verifier() -> HmacWebhookSignatureVerifier:
    return HmacWebhookSignatureVerifier(secret=SECRET, tolerance_seconds=300, clock=lambda: NOW)


@pytest.mark.parametrize('offset', [0, 300, -300])
def test_valid_signature_within_tolerance(verifier: HmacWebhookSignatureVerifier, offset: int) -> None:
    timestamp = str(NOW + offset)

    verifier(BODY, _sign(BODY, timestamp), timestamp)


def test_wrong_secret_is_rejected(verifier: HmacWebhookSignatureVerifier) -> None:
    timestamp = str(NOW)

    with pytest.raises(InvalidSignatureError):
        verifier(BODY, _sign(BODY, timestamp, secret='other'), timestamp)


def test_tampered_body_is_rejected(verifier: HmacWebhookSignatureVerifier) -> None:
    timestamp = str(NOW)
    signature = _sign(BODY, timestamp)

    with pytest.raises(InvalidSignatureError):
        verifier(BODY.replace(b'10.00', b'99.00'), signature, timestamp)


def test_signature_is_bound_to_timestamp(verifier: HmacWebhookSignatureVerifier) -> None:
    signature = _sign(BODY, str(NOW))

    with pytest.raises(InvalidSignatureError):
        verifier(BODY, signature, str(NOW + 1))


@pytest.mark.parametrize('offset', [301, -301, -3600])
def test_stale_or_future_timestamp_is_rejected(verifier: HmacWebhookSignatureVerifier, offset: int) -> None:
    timestamp = str(NOW + offset)

    with pytest.raises(InvalidSignatureError, match='tolerance'):
        verifier(BODY, _sign(BODY, timestamp), timestamp)


@pytest.mark.parametrize(
    ('signature', 'timestamp'),
    [(None, str(NOW)), ('sha256=abc', None), ('', ''), ('sha256=abc', 'not-a-number')],
)
def test_missing_or_malformed_headers_are_rejected(
    verifier: HmacWebhookSignatureVerifier,
    signature: str | None,
    timestamp: str | None,
) -> None:
    with pytest.raises(InvalidSignatureError):
        verifier(BODY, signature, timestamp)
