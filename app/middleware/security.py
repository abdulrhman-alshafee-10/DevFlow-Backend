from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent browsers from MIME-sniffing a response away from the declared content-type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking by ensuring content is not embedded into other sites
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Restrict resources that the browser is allowed to load
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        # Control how much referrer information is included with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Disable access to specific browser features and APIs
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Prevent XSS attacks (though modern browsers prefer CSP)
        response.headers["X-XSS-Protection"] = "0"

        return response
