"""
Compatibility shim for cgi module removed in Python 3.13
This provides the minimal functionality needed by feedparser
"""

import html
import urllib.parse


def escape(s, quote=None):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences."""
    return html.escape(s, quote=quote)


def parse_header(line):
    """Parse a Content-type like header.
    
    Return the main content-type and a dictionary containing
    options.
    """
    parts = line.split(';')
    main_type = parts[0].strip()
    pdict = {}
    for p in parts[1:]:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i+1:].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            pdict[name] = value
    return main_type, pdict


def parse_qs(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace'):
    """Parse a query string given as a string argument."""
    return urllib.parse.parse_qs(qs, keep_blank_values, strict_parsing, encoding, errors)


def parse_qsl(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace'):
    """Parse a query string given as a string argument."""
    return urllib.parse.parse_qsl(qs, keep_blank_values, strict_parsing, encoding, errors)
