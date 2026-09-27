#!/usr/bin/env python3
"""Read-only PDF package checks; not a semantic or visual audit. Requires pypdf."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def normalize(text):
    table = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"',
                          "\u201d": '"', "\u2013": '-', "\u2014": '-',
                          "\u2011": '-', "\u00ad": ''})
    return re.sub(r'\s+', ' ', str(text).translate(table)).strip()


def check(pdf, expected, expected_pages=None, allow_attachments=False):
    from pypdf import PdfReader

    reader = PdfReader(pdf)
    findings = []
    page_refs = {p.indirect_reference.idnum: i for i, p in enumerate(reader.pages)}
    named = reader.named_destinations
    texts = [p.extract_text() or '' for p in reader.pages]
    corpus = normalize('\n'.join(texts))
    dimensions = [[float(x) for x in p.mediabox] for p in reader.pages]
    uris = set()
    links = internal = local = 0

    def fail(message):
        findings.append(message)

    def destination(dest, label):
        if isinstance(dest, str):
            target = named.get(dest) or named.get(dest.lstrip('#'))
            if target is None:
                fail(f'{label}: unknown named destination {dest!r}')
                return
            dest = target.dest_array
        if not isinstance(dest, (list, tuple)) or not dest:
            fail(f'{label}: malformed internal destination')
            return
        page_index = page_refs.get(getattr(dest[0], 'idnum', None))
        if page_index is None:
            fail(f'{label}: destination does not reference a page in this PDF')
            return
        if len(dest) >= 5 and str(dest[1]) == '/XYZ':
            left, bottom, right, top = dimensions[page_index]
            for value, lo, hi, axis in [(dest[2], left, right, 'x'), (dest[3], bottom, top, 'y')]:
                if isinstance(value, (int, float)) and not lo - 1 <= float(value) <= hi + 1:
                    fail(f'{label}: destination {axis} coordinate is outside page {page_index + 1}')

    def local_file(value, label):
        nonlocal local
        uri = urlsplit(value)
        if uri.scheme in ('http', 'https', 'mailto'):
            return
        if uri.scheme not in ('', 'file'):
            return
        if not uri.path:
            return
        local += 1
        path = Path(unquote(uri.path))
        if uri.netloc:
            path = Path('//' + uri.netloc + unquote(uri.path))
        elif sys.platform == 'win32' and re.match(r'^/[A-Za-z]:/', str(path).replace('\\', '/')):
            path = Path(str(path)[1:])
        if not path.is_absolute():
            path = pdf.parent / path
        if not path.is_file():
            fail(f'{label}: missing linked file {value!r}')

    if not reader.pages:
        fail('PDF has no pages')
    if expected_pages is not None and len(reader.pages) != expected_pages:
        fail(f'Expected {expected_pages} pages; found {len(reader.pages)}')
    attachments = len(reader.attachments)
    if attachments and not allow_attachments:
        fail(f'Unexpected attachments: {attachments}')
    for index, page in enumerate(reader.pages, 1):
        if '\ufffd' in texts[index - 1] or '\x00' in texts[index - 1]:
            fail(f'Page {index}: extracted text contains replacement or null characters')
        for ref in page.get('/Annots', []):
            obj = ref.get_object()
            if obj.get('/Subtype') != '/Link':
                continue
            links += 1
            label = f'Page {index}, link {links}'
            if '/Dest' in obj:
                internal += 1
                destination(obj['/Dest'], label)
            elif '/A' in obj:
                action = obj['/A'].get_object()
                if action.get('/S') == '/GoTo':
                    internal += 1
                    destination(action.get('/D'), label)
                elif action.get('/S') == '/URI':
                    uri = str(action.get('/URI', ''))
                    uris.add(uri)
                    if uri.startswith('#'):
                        internal += 1
                        destination(uri[1:], label)
                    else:
                        local_file(uri, label)
                elif action.get('/S') == '/GoToR':
                    file_spec = action.get('/F', '')
                    if hasattr(file_spec, 'get'):
                        file_spec = file_spec.get('/UF') or file_spec.get('/F', '')
                    local_file(str(file_spec), label)

    coverage = {'status': 'not_checked', 'expected': 0, 'found': 0}
    if expected is not None:
        records = expected.get('required_text', [])
        if not isinstance(records, list):
            raise ValueError('required_text must be a list of {id, text} objects')
        seen = set()
        found = 0
        for record in records:
            if not isinstance(record, dict) or not record.get('id') or not normalize(record.get('text', '')):
                raise ValueError('Each required_text record needs a nonempty id and text')
            if record['id'] in seen:
                raise ValueError(f'Duplicate expected-text ID: {record["id"]}')
            seen.add(record['id'])
            if normalize(record['text']) not in corpus:
                fail(f'Missing expected text: {record["id"]}')
            else:
                found += 1
        wanted_uris = expected.get('required_uris', [])
        if not isinstance(wanted_uris, list) or any(not isinstance(u, str) or not u for u in wanted_uris):
            raise ValueError('required_uris must be a list of nonempty strings')
        for uri in wanted_uris:
            if uri not in uris:
                fail(f'Missing expected URI: {uri}')
        coverage = {'status': ('passed' if found == len(records) else 'findings') if records else 'not_checked',
                    'expected': len(records), 'found': found, 'expected_uris': len(wanted_uris)}
    preferences = reader.trailer['/Root'].get('/ViewerPreferences', {})
    if hasattr(preferences, 'get_object'):
        preferences = preferences.get_object()
    return {
        'status': 'passed' if not findings else 'findings',
        'pages': len(reader.pages), 'sheets_duplex': (len(reader.pages) + 1) // 2,
        'page_boxes': sorted(set(tuple(x) for x in dimensions)),
        'links': links, 'internal_links': internal, 'local_file_links': local,
        'attachments': attachments, 'coverage': coverage,
        'duplex': str(preferences.get('/Duplex', 'not_set')),
        'print_scaling': str(preferences.get('/PrintScaling', 'not_set')),
        'size_bytes': pdf.stat().st_size, 'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'findings': findings,
        'limitations': ['No external URLs fetched or source claims verified.',
                        'Exact source-row correspondence and outside folios require separate checks.',
                        'Visual inspection of every page is still required.']
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--expected', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--expect-pages', type=int)
    parser.add_argument('--allow-attachments', action='store_true')
    args = parser.parse_args()
    try:
        pdf = args.pdf.resolve(strict=True)
        expected = json.loads(args.expected.read_text(encoding='utf-8-sig')) if args.expected else None
        if expected is not None and not isinstance(expected, dict):
            raise ValueError('Expected-content file must contain a JSON object')
        if args.report and args.report.resolve() in {pdf, args.expected.resolve() if args.expected else pdf}:
            raise ValueError('Report path must not overwrite an input file')
        if args.expect_pages is not None and args.expect_pages < 1:
            raise ValueError('--expect-pages must be positive')
        result = check(pdf, expected, args.expect_pages, args.allow_attachments)
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.report:
            args.report.write_text(output + '\n', encoding='utf-8')
        print(output)
        return 0 if result['status'] == 'passed' else 1
    except Exception as exc:
        print(json.dumps({'status': 'input_error', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
