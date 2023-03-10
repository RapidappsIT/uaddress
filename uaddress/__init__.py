from __future__ import print_function
from builtins import zip
from builtins import str
import os
import string
import re
import argparse

from .labels import LABELS
from .types import TYPES

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import warnings

import pycrfsuite
import probableparsing

PARENT_LABEL = 'AddressString'
GROUP_LABEL = 'AddressCollection'

MODEL_FILE = 'uaddr.crfsuite'
MODEL_FILES = ''
backupModel = False

regex_tokens = r"\w+(?:\s|\.?)\-(?:\s)\w+|\([0-9а-яА-ЯіІїЇґҐ].*?\)|\(*\b[^\s,;#&]+[.)]*|\/\d+|[№][0-9]*"

try:
    argv = argparse.ArgumentParser(add_help = False)
    argv.add_argument('-m', '--modelfile')

    args, extra = argv.parse_known_args()

    if args.modelfile:
        model = args.modelfile
    else:
        model = os.path.split(os.path.abspath(__file__))[0] + '/' + MODEL_FILE

    TAGGER = pycrfsuite.Tagger()
    TAGGER.open(model)
except IOError:
    warnings.warn('You must train the model (parserator train --trainfile '
                  'FILES) to create the %s file before you can use the parse '
                  'and tag methods' % MODEL_FILE)


def parse(address_string):

    tokens = tokenize(address_string)

    if not tokens:
        return []

    features = tokens2features(tokens)

    tags = TAGGER.tag(features)

    return list(zip(tokens, tags))

def tokenize(address_string):
    if isinstance(address_string, bytes):
        address_string = str(address_string, encoding='utf-8')
    
    re_tokens = re.compile(regex_tokens, re.VERBOSE | re.UNICODE)

    address_string = re.sub(r'\s+', ' ', address_string)
    address_string = fixString(address_string)

    tokens = re_tokens.findall(address_string)
  
    if not tokens:
        return []

    return tokens

def fixString(address):

    ##
    # Unmerge string, if exists housenumber + apartment type
    #
    if re.findall(r'\d{1,}[a-zA-Zа-яА-ЯіІїЇґҐ]{1}[a-zA-Zа-яА-ЯіІїЇґҐ]{1}\s', address):
        address = re.sub(r'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇґҐ]+\s)', ' ', address)

    if re.findall(r'кв\s\d+$', address):
        address = re.sub(r'(?=кв(?:\.|\.?)\s\d+)', ' ', address)
    
    if re.findall(r'(?<=\d[a-zA-Zа-яА-ЯіІїЇґҐ]{1})(?=[a-zA-Zа-яА-ЯіІїЇґҐ]\.\d\s)', address):
        address = re.sub(r'(?<=\d[a-zA-Zа-яА-ЯіІїЇґҐ]{1})(?=[a-zA-Zа-яА-ЯіІїЇґҐ]\.\d\s)', ' ', address)

    if re.findall(r'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇґҐ]{3,}(?:\s|\.\d+$))', address):
        address = re.sub(r'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇґҐ]{3,}(?:\s|\.\d+$))', ' ', address)

    if re.findall(r'\d+[a-zA-Zа-яА-ЯіІїЇґҐ]\.\d+', address):
        address = re.sub(r'(?<=\d)(?=[a-zA-Zа-яА-ЯіІїЇґҐ]\.\d+)', ' ', address)

    if re.findall(r'(?<=[a-zA-Zа-яА-ЯіІїЇґҐ]\.)(?=\d+(?:\s|\,))', address):
        address = re.sub(r'(?<=[a-zA-Zа-яА-ЯіІїЇґҐ]\.)(?=\d+(?:\s|\,))', ' ', address)

    if re.findall(r'[a-zA-Zа-яА-ЯіІїЇґҐ]{1,}\s[a-zA-Zа-яА-ЯіІїЇґҐ]{1,}\d\s', address):
        address = re.sub(r'(?<=[a-zA-Zа-яА-ЯіІїЇґҐ])(?=\d\s)', ' ', address)

    if re.findall(r'(?<=\d{5})', address):
        address = re.sub(r'(?<=\d{5})', ' ', address)

    if re.findall(r'\.(?!\s)', address):
        address = re.sub(r'\.(?!\s)', '. ', address)

    ##
    # ADDING SPACE BEFORE BRACKET
    #
    if re.findall(r'(?<=[a-zA-Zа-яА-ЯіІїЇґҐ])\(', address):
        address = re.sub(r'(?<=[a-zA-Zа-яА-ЯіІїЇґҐ])\(', ' (', address)

    ##
    # REMOVE SPACE AFTER HYPHEN
    #
    if re.findall(r'\-\s+', address):
        address = re.sub('\-\s+', '-', address)

    ##
    # ADD SPACE BEFORE AND AFTER BRACKET
    #
    if re.findall(r'(?=\()|(?<=\))', address):
        address = re.sub('(?=\()|(?<=\))', ' ', address)

    return address

def tokenFeatures(token):

    token_clean = re.sub(r'(^[\W]*)|([^.\w]*$)', u'', token, flags=re.UNICODE)

    token_abbrev = re.sub(r'[,]', u'', token_clean.lower())

    features = {
   
        'abbrev': token_clean.endswith('.'),
   
        'digits': digits(token_clean),
   
        'word': (token_abbrev
                 if not token_abbrev.isdigit()
                 else False),

        'length': (u'd:' + str(len(token_abbrev))
                   if token_abbrev.isdigit()
                   else u'w:' + str(len(token_abbrev))),
   
        'endsinpunc': (token[-1]
                       if bool(re.match(r'.+[^.\w]', token, flags=re.UNICODE))
                       else False),

        'types': token_abbrev in TYPES
   
    }

    return features

def tokens2features(address):

    feature_sequence = [tokenFeatures(address[0])]
    previous_features = feature_sequence[-1].copy()

    for token in address[1:]:
        token_features = tokenFeatures(token)
        current_features = token_features.copy()

        feature_sequence[-1]['next'] = current_features
        token_features['previous'] = previous_features

        feature_sequence.append(token_features)

        previous_features = current_features

    feature_sequence[0]['address.start'] = True
    feature_sequence[-1]['address.end'] = True

    if len(feature_sequence) > 1:
        feature_sequence[1]['previous']['address.start'] = True
        feature_sequence[-2]['next']['address.end'] = True

    return feature_sequence


def digits(token):
    if token.isdigit():
        return 'all_digits'
    elif set(token) & set(string.digits):
        return 'some_digits'
    else:
        return 'no_digits'


class RepeatedLabelError(probableparsing.RepeatedLabelError):
 
    REPO_URL = 'https://github.com/RapidappsIT/uaddress/issues/new'
    DOCS_URL = ''
