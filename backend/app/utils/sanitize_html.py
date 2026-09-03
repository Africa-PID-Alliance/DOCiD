"""Sanitizer for author-supplied rich-text HTML (publication and file descriptions).

These fields come from the TipTap editor in frontend/src/components/RichTextEditor.jsx
and are rendered with dangerouslySetInnerHTML on the public DOCiD page, so anything
stored unsanitized is stored XSS against every visitor. Sanitizing on write is the
primary defence; frontend/src/lib/sanitizeRichText.js re-sanitizes on render to also
cover rows written before this existed.
"""

import bleach
from bleach.css_sanitizer import CSSSanitizer

# Tags the TipTap toolbar can actually produce (StarterKit + Heading, TextStyle,
# FontFamily, TextAlign, Link, Underline).
ALLOWED_TAGS = [
    'p', 'br', 'span', 'div',
    'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'sub', 'sup',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr', 'a',
]

ALLOWED_ATTRIBUTES = {
    '*': ['style', 'class', 'title'],
    'a': ['href', 'target', 'rel', 'style', 'class', 'title'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'tel']

# bleach 5+ empties every style="" unless a css_sanitizer is supplied, which would
# silently strip the editor's alignment and font choices.
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=[
        'text-align', 'font-family', 'font-size', 'font-style', 'font-weight',
        'color', 'background-color', 'text-decoration', 'line-height',
        'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
        'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    ],
)


def sanitize_rich_text(raw_html):
    """Strip scripts, event handlers and unsafe URLs from author-supplied HTML.

    Returns None/'' unchanged so callers can keep distinguishing "not supplied"
    from "supplied but empty".
    """
    if not raw_html:
        return raw_html

    return bleach.clean(
        str(raw_html),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=CSS_SANITIZER,
        strip=True,
    )
