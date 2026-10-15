from fastapi import Request
from slowapi import Limiter


def client_ip(request: Request) -> str:
    """Client IP for rate limiting.

    Behind Render's proxy the socket address is the proxy itself, so read
    X-Forwarded-For. The last entry is the one the proxy appended, which a
    caller cannot forge (the earlier entries can be).
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def global_key(request: Request) -> str:
    """One shared bucket: a cap that holds even if callers spoof their IP.

    The parameter must be named `request`: slowapi only passes the request to a
    per-limit key function when it sees a parameter with that exact name.
    """
    return "global"


limiter = Limiter(key_func=client_ip)
