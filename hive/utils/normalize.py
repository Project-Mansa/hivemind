"""Methods to parse steemd values and clean strings."""

import math
import decimal
from datetime import datetime
import ujson as json

NAI_MAP = {
    '@@000000013': 'SBD',
    '@@000000021': 'STEEM',
    '@@000000037': 'VESTS',
}

def vests_amount(value):
    """Returns a decimal amount, asserting units are VESTS"""
    return parse_amount(value, 'VESTS')

def steem_amount(value):
    """Returns a decimal amount, asserting units are STEEM"""
    return parse_amount(value, 'STEEM')

def sbd_amount(value):
    """Returns a decimal amount, asserting units are SBD"""
    return parse_amount(value, 'SBD')

def parse_amount(value, expected_unit=None):
    """Parse steemd-style amout/asset value, return (decimal, name)."""
    if isinstance(value, dict):
        value = [value['amount'], value['precision'], value['nai']]

    if isinstance(value, str):
        raw_amount, unit = value.split(' ')
        dec_amount = decimal.Decimal(raw_amount)

    elif isinstance(value, list):
        satoshis, precision, nai = value
        dec_amount = decimal.Decimal(satoshis) / (10**precision)
        assert nai in NAI_MAP, "unknown NAI %s; expected %s" % (
            nai, expected_unit or '(any)')
        unit = NAI_MAP[nai]

    else:
        raise Exception("invalid input amount %s" % repr(value))

    if expected_unit:
        assert unit == expected_unit
        return dec_amount

    return (dec_amount, unit)

def amount(string):
    """Parse a steemd asset-amount as a Decimal(). Discard asset type."""
    return parse_amount(string)[0]

def legacy_amount(value):
    """Get a pre-appbase-style amount string given a (numeric, asset-str)."""
    if isinstance(value, str):
        return value # already legacy
    amt, asset = parse_amount(value)
    prec = {'SBD': 3, 'STEEM': 3, 'VESTS': 6}[asset]
    tmpl = ("%%.%df %%s" % prec)
    return tmpl % (amt, asset)

def block_num(block):
    """Given a block object, returns the block number."""
    return int(block['block_id'][:8], base=16)

def block_date(block):
    """Parse block timestamp into datetime object."""
    return parse_time(block['timestamp'])

def parse_time(block_time):
    """Convert chain date into datetime object."""
    return datetime.strptime(block_time, '%Y-%m-%dT%H:%M:%S')

def load_json_key(obj, key):
    """Given a dict, parse JSON in `key`. Blank dict on failure."""
    if not obj[key]:
        return {}
    ret = {}
    try:
        ret = json.loads(obj[key])
    except Exception:
        return {}
    return ret

def trunc(string, maxlen):
    """Truncate a string, with a 3-char penalty if maxlen exceeded."""
    if string:
        string = string.strip()
        if len(string) > maxlen:
            string = string[0:(maxlen-3)] + '...'
    return string


def rep_log10(rep):
    """Convert raw steemd rep into a UI-ready value centered at 25."""
    def _log10(string):
        leading_digits = int(string[0:4])
        log = math.log10(leading_digits) + 0.00000001
        num = len(string) - 1
        return num + (log - int(log))

    rep = str(rep)
    if rep == "0":
        return 25

    sign = -1 if rep[0] == '-' else 1
    if sign < 0:
        rep = rep[1:]

    out = _log10(rep)
    out = max(out - 9, 0) * sign  # @ -9, $1 earned is approx magnitude 1
    out = (out * 9) + 25          # 9 points per magnitude. center at 25
    return round(out, 2)


def safe_img_url(url, max_size=1024):
    """Given an image URL, strict enforce size and validity."""
    if (url and isinstance(url, str)
            and len(url) < max_size
            and url[0:4] == 'http'):
        return url.strip()
    return None
