import DOMPurify from 'isomorphic-dompurify';

/**
 * Tags and attributes the TipTap editor in RichTextEditor.jsx can actually
 * produce (StarterKit + Heading, TextStyle, FontFamily, TextAlign, Link,
 * Underline). Anything outside this set is dropped rather than rendered.
 */
const ALLOWED_RICH_TEXT_TAGS = [
  'p', 'br', 'span', 'div',
  'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'sub', 'sup',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr', 'a',
];

const ALLOWED_RICH_TEXT_ATTRIBUTES = ['href', 'target', 'rel', 'style', 'class', 'title'];

/**
 * Sanitize stored rich-text HTML before it reaches dangerouslySetInnerHTML.
 *
 * Descriptions are author-supplied HTML rendered on the public DOCiD page, so
 * unsanitized output is stored XSS against every visitor. The backend
 * sanitizes on write (see backend/app/utils/sanitize_html.py); this is the
 * second layer that also covers rows stored before that existed.
 */
export function sanitizeRichText(rawHtml) {
  if (!rawHtml) return '';

  return DOMPurify.sanitize(String(rawHtml), {
    ALLOWED_TAGS: ALLOWED_RICH_TEXT_TAGS,
    ALLOWED_ATTR: ALLOWED_RICH_TEXT_ATTRIBUTES,
    // DOMPurify's default URI allowlist already blocks javascript:/data: hrefs.
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input'],
    FORBID_ATTR: ['srcset', 'formaction', 'xlink:href'],
  });
}

export default sanitizeRichText;
