"""Auth placeholder.

TODO(auth): implement real JWT verification here.
"""


def decode_token(token: str) -> dict:
    """Stub token decoder.  Returns a hardcoded payload for local development."""
    # TODO(auth): verify signature, expiry, issuer
    return {
        "sub": "user-riya-sharma-001",
        "name": "Riya Sharma",
        "role": "executive",
        "tenant_id": "bt-tenant-001",
        "city": "Mumbai",
    }
