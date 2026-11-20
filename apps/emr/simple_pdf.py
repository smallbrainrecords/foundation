"""A small text PDF writer, standard library only (2026-11-17).

The server has no PDF library (the fax and editing work cut PDFs on the
Mac). A completed check-in form is filed to the chart by the server itself,
because nobody may be at a Mac when the patient finishes, so it needs to
draw one simple document: a title, a few lines of who and when, an optional
photo, and question / answer pairs. The text is real PDF text (Helvetica),
so it can be selected and searched.

Characters outside Windows-1252 print as "?". Lines wrap on spaces by the
Helvetica character widths; a word longer than a line is cut.
"""
import io

PAGE_W, PAGE_H = 612, 792
MARGIN = 54

# Helvetica widths (thousandths of the font size) for ASCII 32..126.
_HELV = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,
]


def text_width(text, size, bold=False):
    total = 0
    for ch in text:
        code = ord(ch)
        total += _HELV[code - 32] if 32 <= code <= 126 else 556
    # Helvetica-Bold runs about 7% wider; over-estimating only wraps earlier.
    return total * size / 1000.0 * (1.08 if bold else 1.0)


def wrap(text, size, width, bold=False):
    """Lines that fit `width` points; explicit newlines are kept."""
    out = []
    for paragraph in str(text).split('\n'):
        words = paragraph.split(' ')
        line = ''
        for word in words:
            candidate = word if not line else line + ' ' + word
            if text_width(candidate, size, bold) <= width:
                line = candidate
                continue
            if line:
                out.append(line)
            while text_width(word, size, bold) > width:
                cut = len(word)
                while cut > 1 and text_width(word[:cut], size, bold) > width:
                    cut -= 1
                out.append(word[:cut])
                word = word[cut:]
            line = word
        out.append(line)
    return out


def _pdf_string(text):
    raw = text.encode('cp1252', errors='replace')
    raw = raw.replace(b'\\', b'\\\\').replace(b'(', b'\\(').replace(b')', b'\\)')
    raw = raw.replace(b'\r', b'').replace(b'\n', b' ')
    return b'(' + raw + b')'


class Document:
    """Add blocks top to bottom; `render()` returns the PDF bytes."""

    def __init__(self):
        self._pages = []
        self._image = None  # (jpeg bytes, width px, height px, page index, x, y, w, h)
        self._new_page()

    def _new_page(self):
        self._pages.append([])
        self._y = PAGE_H - MARGIN

    def _ensure(self, height):
        if self._y - height < MARGIN:
            self._new_page()

    def text(self, text, size=11, bold=False, gap_after=4, indent=0, width=None):
        width = width or (PAGE_W - 2 * MARGIN - indent)
        leading = size * 1.3
        for line in wrap(text, size, width, bold):
            self._ensure(leading)
            self._y -= leading
            font = b'/F2' if bold else b'/F1'
            self._pages[-1].append(
                b'BT ' + font + b' %d Tf %.2f %.2f Td ' % (size, MARGIN + indent, self._y)
                + _pdf_string(line) + b' Tj ET')
        self._y -= gap_after

    def space(self, points):
        self._y -= points

    def image_top_right(self, jpeg, width_px, height_px, box=140):
        """A JPEG in the top-right corner of the current page, at most
        `box` points on its longer side. Call before the text it sits
        beside; returns the width the text should leave free."""
        scale = box / float(max(width_px, height_px))
        w, h = width_px * scale, height_px * scale
        x = PAGE_W - MARGIN - w
        y = PAGE_H - MARGIN - h
        self._image = (jpeg, width_px, height_px, len(self._pages) - 1, x, y, w, h)
        return w + 18

    def below_image(self, gap=12):
        """Move down past the photo, if it is on this page and lower."""
        if self._image and self._image[3] == len(self._pages) - 1:
            bottom = self._image[5]
            if self._y > bottom - gap:
                self._y = bottom - gap

    def render(self):
        objects = []

        def add(body):
            objects.append(body)
            return len(objects)

        font1 = add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
        font2 = add(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
        image_ref = None
        if self._image:
            jpeg, wpx, hpx = self._image[:3]
            image_ref = add(
                b'<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceRGB '
                b'/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n' % (wpx, hpx, len(jpeg))
                + jpeg + b'\nendstream')
        pages_index = add(None)  # filled below
        page_refs = []
        for index, ops in enumerate(self._pages):
            content = list(ops)
            resources = b'/Font << /F1 %d 0 R /F2 %d 0 R >>' % (font1, font2)
            if self._image and self._image[3] == index:
                _, _, _, _, x, y, w, h = self._image
                content.insert(0, b'q %.2f 0 0 %.2f %.2f %.2f cm /Im1 Do Q' % (w, h, x, y))
                resources += b' /XObject << /Im1 %d 0 R >>' % image_ref
            stream = b'\n'.join(content)
            content_ref = add(b'<< /Length %d >>\nstream\n' % len(stream) + stream + b'\nendstream')
            page_refs.append(add(
                b'<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Resources << %s >> /Contents %d 0 R >>'
                % (pages_index, PAGE_W, PAGE_H, resources, content_ref)))
        objects[pages_index - 1] = (
            b'<< /Type /Pages /Kids [' + b' '.join(b'%d 0 R' % r for r in page_refs)
            + b'] /Count %d >>' % len(page_refs))
        catalog = add(b'<< /Type /Catalog /Pages %d 0 R >>' % pages_index)

        out = io.BytesIO()
        out.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(out.tell())
            out.write(b'%d 0 obj\n' % number + body + b'\nendobj\n')
        xref = out.tell()
        out.write(b'xref\n0 %d\n0000000000 65535 f \n' % (len(objects) + 1))
        for offset in offsets:
            out.write(b'%010d 00000 n \n' % offset)
        out.write(b'trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n'
                  % (len(objects) + 1, catalog, xref))
        return out.getvalue()
