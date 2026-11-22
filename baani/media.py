"""Serve uploaded files to authenticated users, including with DEBUG disabled."""
import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe


@require_safe
def uploaded_media(request, path):
    if not request.user.is_authenticated or not request.user.is_active:
        raise PermissionDenied

    try:
        relative = Path(path)
        if relative.is_absolute() or any(part.startswith('.') for part in relative.parts):
            raise Http404
        root = Path(settings.MEDIA_ROOT).resolve()
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise Http404
        stream = target.open('rb')
    except (OSError, ValueError):
        raise Http404 from None

    content_type = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
    inline = content_type in {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif',
        'image/bmp', 'image/tiff', 'image/x-icon', 'image/vnd.microsoft.icon',
    }
    response = FileResponse(stream, content_type=content_type,
                            as_attachment=not inline, filename=target.name)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    return response
