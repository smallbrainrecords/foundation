"""Sending a fax through RingCentral, and asking what became of it.

One server credential (a JWT for the extension that owns the clinic fax
number) sends every fax, so the sender's number is always the clinic's. The
three values come from the environment: RINGCENTRAL_CLIENT_ID,
RINGCENTRAL_CLIENT_SECRET, RINGCENTRAL_JWT. With any of them missing,
`is_configured()` is false and nothing here makes a request.

Facts taken from RingCentral's developer guide on 2026-11-12:
  - token: POST /restapi/oauth/token, Basic client id:secret,
    grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer, assertion=<JWT>;
    the access token lasts about two hours and the token call is rate
    limited, so one token is kept and reused.
  - send: POST /restapi/v1.0/account/~/extension/~/fax as multipart/form-data
    with flat parts `to`, `faxResolution`, `attachment`; the answer carries
    the message `id`.
  - status: GET /restapi/v1.0/account/~/extension/~/message-store/<id>,
    `messageStatus` is "Queued" until it settles.
  - limits: 50 MB and 200 pages per fax; a 429 carries Retry-After.

Confirmed from RingCentral's OpenAPI spec (rc-platform.yml, read 2026-11-12):
  - `coverIndex` 0 attaches no cover page; left out, the account's default
    cover page is attached.
  - an outbound fax's `messageStatus` is "Queued" while any recipient is
    queued, "SendingFailed" if any failed, otherwise "Sent"; each `to[]`
    entry carries its own `messageStatus` and a `faxErrorCode` (LineBusy,
    NoAnswer, NoFaxMachine, InvalidNumber, ...).
  - personal contacts: GET .../address-book/contact (permission
    ReadContacts, "Heavy" rate group, up to 1000 a page), with `firstName`,
    `lastName`, `company`, `businessFax`, `otherFax`.
  - sent faxes: GET .../message-store?messageType=Fax&direction=Outbound
    (permission ReadMessages, "Light" group); without `dateFrom` it covers
    only the last 24 hours.

`_state_for` still reads any status containing "fail" as failed and leaves
an unknown one queued, so a status RingCentral adds later cannot be read as
delivered.

Standard library only: nothing here is worth a new dependency.
"""
import base64
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_SERVER = 'https://platform.ringcentral.com'
TIMEOUT_SECONDS = 30

QUEUED = 'queued'
DELIVERED = 'delivered'
FAILED = 'failed'


class FaxNotConfigured(Exception):
    """The RingCentral credential is not set on this server."""


class FaxError(Exception):
    """RingCentral refused the request or could not be reached."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


_token_lock = threading.Lock()
_token = {'value': None, 'expires': 0.0}


def _config():
    cfg = {
        'client_id': os.environ.get('RINGCENTRAL_CLIENT_ID', '').strip(),
        'client_secret': os.environ.get('RINGCENTRAL_CLIENT_SECRET', '').strip(),
        'jwt': os.environ.get('RINGCENTRAL_JWT', '').strip(),
        'server': os.environ.get('RINGCENTRAL_SERVER', '').strip() or DEFAULT_SERVER,
    }
    return cfg


def is_configured():
    cfg = _config()
    return bool(cfg['client_id'] and cfg['client_secret'] and cfg['jwt'])


def _http(method, url, headers, body=None):
    """One request. Returns (status, parsed JSON or {}). The seam tests
    replace; raises FaxError only when no answer came back at all."""
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        raw = error.read()
        status = error.code
    except (urllib.error.URLError, OSError) as error:
        raise FaxError('RingCentral could not be reached: %s' % error)
    try:
        parsed = json.loads(raw) if raw else {}
    except ValueError:
        parsed = {}
    return status, parsed if isinstance(parsed, dict) else {}


def _message(parsed, status):
    return (parsed.get('message') or parsed.get('error_description')
            or parsed.get('error') or 'HTTP %s' % status)


def _access_token(force=False):
    cfg = _config()
    if not is_configured():
        raise FaxNotConfigured()
    with _token_lock:
        if not force and _token['value'] and time.time() < _token['expires']:
            return _token['value']
        basic = base64.b64encode(
            ('%s:%s' % (cfg['client_id'], cfg['client_secret'])).encode()).decode()
        body = urllib.parse.urlencode({
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': cfg['jwt'],
        }).encode()
        status, parsed = _http('POST', cfg['server'] + '/restapi/oauth/token', {
            'Authorization': 'Basic ' + basic,
            'Content-Type': 'application/x-www-form-urlencoded',
        }, body)
        if status != 200 or not parsed.get('access_token'):
            raise FaxError('RingCentral sign-in failed: %s' % _message(parsed, status), status)
        _token['value'] = parsed['access_token']
        # Renew five minutes early; never trust a lifetime under a minute.
        _token['expires'] = time.time() + max(60, int(parsed.get('expires_in', 3600)) - 300)
        return _token['value']


def forget_token():
    with _token_lock:
        _token['value'] = None
        _token['expires'] = 0.0


def _authorized(method, path, headers=None, body=None):
    cfg = _config()
    for attempt in (0, 1):
        token = _access_token(force=attempt == 1)
        merged = dict(headers or {})
        merged['Authorization'] = 'Bearer ' + token
        status, parsed = _http(method, cfg['server'] + path, merged, body)
        if status == 401 and attempt == 0:
            continue
        return status, parsed
    return status, parsed


def build_multipart(fields, pdf_bytes, filename):
    """multipart/form-data body: the flat fields, then the PDF as
    `attachment`. Returns (content type, body bytes)."""
    boundary = 'smallbrain-' + uuid.uuid4().hex
    parts = []
    for name, value in fields:
        parts.append((
            '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
            % (boundary, name, value)).encode())
    parts.append((
        '--%s\r\nContent-Disposition: form-data; name="attachment"; filename="%s"\r\n'
        'Content-Type: application/pdf\r\n\r\n' % (boundary, filename)).encode())
    parts.append(pdf_bytes)
    parts.append(('\r\n--%s--\r\n' % boundary).encode())
    return 'multipart/form-data; boundary=' + boundary, b''.join(parts)


def _state_for(rc_status):
    text = (rc_status or '').lower()
    if 'fail' in text:
        return FAILED
    if text in ('sent', 'delivered'):
        return DELIVERED
    return QUEUED


def _reading(parsed):
    """What a RingCentral message record says, in our terms."""
    rc_status = parsed.get('messageStatus') or ''
    error = ''
    recipients = parsed.get('to') or []
    if recipients and isinstance(recipients[0], dict):
        first = recipients[0]
        error = first.get('faxErrorCode') or ''
        # The per-recipient status is the one that says a fax failed when
        # the message as a whole still reads "Sent".
        if _state_for(first.get('messageStatus')) == FAILED:
            rc_status = first.get('messageStatus')
    return {
        'state': _state_for(rc_status),
        'rc_status': rc_status,
        'error': error,
        'page_count': parsed.get('faxPageCount'),
    }


def send_fax(pdf_bytes, to_number, filename='requisition.pdf'):
    """Hand one PDF to RingCentral for `to_number` (digits with country
    code), with no cover page. Returns {'message_id', 'state', 'rc_status',
    'error', 'page_count'}. Raises FaxNotConfigured or FaxError."""
    content_type, body = build_multipart(
        [('to', to_number), ('faxResolution', 'High'), ('coverIndex', '0')],
        pdf_bytes, filename)
    status, parsed = _authorized(
        'POST', '/restapi/v1.0/account/~/extension/~/fax',
        {'Content-Type': content_type}, body)
    if status not in (200, 201) or not parsed.get('id'):
        raise FaxError('RingCentral did not accept the fax: %s' % _message(parsed, status), status)
    reading = _reading(parsed)
    reading['message_id'] = str(parsed['id'])
    return reading


def message_status(message_id):
    """Where a sent fax stands now. Same keys as `send_fax` minus the id."""
    status, parsed = _authorized(
        'GET', '/restapi/v1.0/account/~/extension/~/message-store/%s'
        % urllib.parse.quote(str(message_id)))
    if status != 200:
        raise FaxError('RingCentral did not report on the fax: %s' % _message(parsed, status), status)
    return _reading(parsed)


# ---------- Reading what the clinic already has in RingCentral ----------

# Pages are capped so a huge address book or history can never turn one
# request into dozens: contacts are in the "Heavy" group (10 calls a minute).
_CONTACT_PAGE_SIZE = 1000
_CONTACT_MAX_PAGES = 3
_HISTORY_PAGE_SIZE = 1000
_HISTORY_MAX_PAGES = 5
HISTORY_DAYS = 365


def _paged(path, query, max_pages):
    """Records from a paged RingCentral list, following page numbers."""
    records = []
    for page in range(1, max_pages + 1):
        params = dict(query, page=page)
        status, parsed = _authorized('GET', path + '?' + urllib.parse.urlencode(params))
        if status != 200:
            raise FaxError('RingCentral did not answer: %s' % _message(parsed, status), status)
        batch = parsed.get('records') or []
        records.extend(r for r in batch if isinstance(r, dict))
        paging = parsed.get('paging') or {}
        if not batch or page >= int(paging.get('totalPages') or 1):
            break
    return records


def contact_fax_numbers():
    """Every fax number in the credential owner's personal RingCentral
    contacts: [{'fax_number': as stored there, 'name', 'note'}]. A contact
    with a business fax and another fax gives two entries.

    The name is the company when there is one, since a fax goes to a place;
    the person is then the note. Only the address book of the user who
    created the JWT is visible: RingCentral contacts are per user.
    """
    found = []
    records = _paged(
        '/restapi/v1.0/account/~/extension/~/address-book/contact',
        {'perPage': _CONTACT_PAGE_SIZE}, _CONTACT_MAX_PAGES)
    for record in records:
        person = ' '.join(
            part for part in (
                (record.get('firstName') or '').strip(),
                (record.get('lastName') or '').strip()) if part)
        company = (record.get('company') or '').strip()
        name = company or person
        note = person if company and person else ''
        for key in ('businessFax', 'otherFax'):
            number = (record.get(key) or '').strip()
            if number:
                found.append({'fax_number': number, 'name': name, 'note': note})
    return found


def sent_fax_numbers(days=HISTORY_DAYS):
    """Where the clinic's faxes went in the last `days`:
    [{'fax_number', 'name', 'times_faxed', 'times_delivered', 'last_faxed'}],
    one entry per number as RingCentral wrote it.

    `times_delivered` counts only faxes RingCentral reports as sent to that
    recipient, so a number that only ever failed is not taken as proven.
    """
    import datetime
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    records = _paged(
        '/restapi/v1.0/account/~/extension/~/message-store',
        {'messageType': 'Fax', 'direction': 'Outbound', 'dateFrom': since,
         'perPage': _HISTORY_PAGE_SIZE}, _HISTORY_MAX_PAGES)
    by_number = {}
    for record in records:
        created = record.get('creationTime') or ''
        for party in record.get('to') or []:
            if not isinstance(party, dict):
                continue
            number = (party.get('phoneNumber') or '').strip()
            if not number:
                continue
            entry = by_number.setdefault(number, {
                'fax_number': number, 'name': '', 'times_faxed': 0,
                'times_delivered': 0, 'last_faxed': ''})
            entry['times_faxed'] += 1
            state = _state_for(party.get('messageStatus') or record.get('messageStatus'))
            if state == DELIVERED:
                entry['times_delivered'] += 1
            if not entry['name'] and (party.get('name') or '').strip():
                entry['name'] = party['name'].strip()
            if created > entry['last_faxed']:
                entry['last_faxed'] = created
    return list(by_number.values())
