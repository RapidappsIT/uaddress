from builtins import zip, str
import os
import re
import argparse
import string
import warnings

from collections import OrderedDict

import pycrfsuite
import probableparsing

from .labels import LABELS
from .types import TYPES


PARENT_LABEL = 'AddressString'
GROUP_LABEL = 'AddressCollection'

DEFAULT_MODEL_FILE = 'uaddr.crfsuite'
MODEL_FILES = ''
backupModel = False

REGEX_TOKENS = re.compile(
    rf"""
    \w+(?:\s|\.?)\-(?:\s)\w+|\([0-9а-яА-ЯіІїЇґҐ].*?\)|\(*\b[^\s,;#&]+[.)]*|\/\d+|[№][0-9]*|\d+(?:\s|\.?)\-(?:\s)?[а-яА-Яa-zA-Z]+
    """,
    re.VERBOSE | re.UNICODE,
)

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-m', '--modelfile', help='Path to the CRF model file')
    args, _ = parser.parse_known_args()
    return args


def load_tagger(model_path):
    tagger = pycrfsuite.Tagger()
    tagger.open(model_path)
    return tagger


def validate_tags(tags):
    return [tag if tag in LABELS else 'NotAddress' for tag in tags]


def digits(token: str) -> str:
    if token.isdigit():
        return 'all_digits'
    elif any(ch.isdigit() for ch in token):
        return 'some_digits'
    else:
        return 'no_digits'


def token_features(token: str) -> dict:
    token_clean = re.sub(r'(^[\W]*)|([^.\w]*$)', '', token, flags=re.UNICODE)
    token_abbrev = token_clean.lower()

    type_label = None

    if re.fullmatch(r'\d{5}', token_abbrev):
        type_label = 'PostCode'
    else:
        for category, terms in TYPES.items():
            if token_abbrev in terms:
                type_label = category
                break

    return {
        'abbrev': token_clean.endswith('.'),
        'digits': digits(token_clean),
        'word': token_abbrev if not token_abbrev.isdigit() else False,
        'length': ('d:' if token_abbrev.isdigit() else 'w:') + str(len(token_abbrev)),
        'endsinpunc': token[-1] if re.match(r'.+[^.\w]', token, flags=re.UNICODE) else False,
        'type': type_label or 'none'
    }


def tokens2features(tokens: list[str]) -> list[dict]:
    features_sequence = []

    for i, token in enumerate(tokens):
        features = token_features(token)

        if i == 0:
            features['address.start'] = True
        if i == len(tokens) - 1:
            features['address.end'] = True

        if i > 0:
            features['previous_token'] = tokens[i - 1]
        if i < len(tokens) - 1:
            features['next_token'] = tokens[i + 1]

        features_sequence.append(features)

    return features_sequence

def _alpha_len(s: str) -> int:
    return len(re.sub(r"[.\-_/ ]", "", s, flags=re.UNICODE))

def _punct_count(s: str) -> int:
    return sum(s.count(p) for p in ".-_/")

def _build_pattern(street_types: set[str]) -> str:
    uniq = list(dict.fromkeys(street_types))
    sorted_types = sorted(
        uniq, key=lambda s: (_alpha_len(s), _punct_count(s), len(s)), reverse=True
    )
    return "|".join(re.escape(t) for t in sorted_types)

def _build_glueable_pattern(street_types: set[str]) -> str:
    uniq = list(dict.fromkeys(street_types))
    glue = [t for t in uniq if any(ch in t for ch in ('.', '-', '/', '\\'))]
    glue_sorted = sorted(
        glue, key=lambda s: (_alpha_len(s), _punct_count(s), len(s)), reverse=True
    )
    return "|".join(re.escape(t) for t in glue_sorted)

def fix_string(address: str) -> str:
    address = re.sub(r'[\u00A0\u202F\u2007]', ' ', address)
    address = re.sub(r'(?<=\d)\u02BC(?=\d)', '/', address)

    APOST = "\u02BC\u2019'"
    LETTERS = f"A-Za-zА-Яа-яІіЇїЄєҐґ{APOST}"

    types_pattern = _build_pattern(TYPES['StreetType'])
    types_glueable_pattern = _build_glueable_pattern(TYPES['StreetType'])

    regex_chain = [
        (rf'(?<![{LETTERS}\.])({types_glueable_pattern})(?=[{LETTERS}])', r'\1 '),
        (rf'(?<![{LETTERS}])({types_pattern})(?![{LETTERS}])(?=(?!-)[^\s\u00A0\u202F\u2007])', r'\1 '),
        (rf'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]+\s)', ' '),
        (r'(?=кв(?:\.|\.?)\s*\d+)', ' '),
        (rf'(?<=\d[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]{{1}})(?=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]\.\d\s)', ' '),
        (rf'(?<=[0-9][a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}])(?=блок)', ' '),
        (rf'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]{{3,}}(?:\s|\.\d+$))', ' '),
        (rf'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]\.\d+)', ' '),
        (rf'(?<=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}]\.)(?=\d+(?:\s|,))', ' '),
        (rf'(?<=[a-zA-Zа-яА-ЯіІїЇєЄґҐ{APOST}])(?=\d\s)', ' '),
        (r'(?<=\b\d{5})(?!\d)', ' '),
        (r'\.(?!\s)', '. '),
        (r'(?<=\№)(?=кв)', ' '),
        (rf'\b(буд|корп|під{APOST}?їзд|під|поверх|блок)(?=\d)', r'\1 '),
        (r'(?=\()|(?<=\))', ' '),
        (r'\-\s+', '-'),
        (rf'(?<=\d)[{APOST}]', ' ')
    ]

    for pat, repl in regex_chain:
        address = re.sub(pat, repl, address, flags=re.IGNORECASE | re.UNICODE)

    address = re.sub(r'\s{2,}', ' ', address).strip()
    address = re.sub(r'\s+,', ', ', address)
    address = re.sub(r',\s+', ', ', address)

    return address


def tokenize(address_string: str) -> list[str]:
    if isinstance(address_string, bytes):
        address_string = address_string.decode('utf-8')

    address_string = re.sub(r'\s+', ' ', address_string)
    address_string = fix_string(address_string)

    tokens = [t.strip() for t in re.findall(REGEX_TOKENS, address_string) if t.strip() and t != '.']

    return tokens or []


def parse(address_string: str) -> list[tuple[str, str]]:
    tokens = tokenize(address_string)
    
    if not tokens:
        return []

    features = tokens2features(tokens)
    tags = TAGGER.tag(features)
    tags = validate_tags(tags)

    return list(zip(tokens, tags))


args = parse_args()
model_path = args.modelfile or os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_MODEL_FILE)

try:
    TAGGER = load_tagger(model_path)
except IOError:
    warnings.warn(
        f'You must train the model (parserator train --trainfile FILES) '
        f'to create the model file before using parse/tag methods: {model_path}'
    )
    TAGGER = None
