
from __future__ import print_function
from builtins import zip
from builtins import str
import os
import string
import re
import argparse

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import warnings

import pycrfsuite
import probableparsing

# The address components 

LABELS = [

    'Country',
    'RegionType',
    'Region',
    'CountyType',
    'County',
    'SubLocalityType',
    'SubLocality',
    'LocalityType',
    'Locality',
    'StreetType',
    'Street',
    'HousingType',
    'Housing',
    'HostelType',
    'Hostel',
    'HouseNumberType',
    'HouseNumber',
    'HouseNumberAdditionally',
    'SectionType',
    'Section',
    'ApartmentType',
    'Apartment',
    'RoomType',
    'Room',
    'Sector',
    'FloorType',
    'Floor',
    'PostCode',
    'Manually',
    'NotAddress',
    'Comment',
    'AdditionalData'
    
]

PARENT_LABEL = 'AddressString'
GROUP_LABEL = 'AddressCollection'

MODEL_FILE = 'uaddr.crfsuite'
MODEL_FILES = ''
backupModel = False

TYPES = {

    # REGION
    "обл", "обл.", "область",
    # CITY
    "м", "м.", "місто", "г", "г.", "город",
    # DISTRICT
    "р-н", "р-н.", "рн", "рн.", "р-он", "район",
    # MICRODISTRICT
    "мікр", "мікр.", "мн", "мр", "мкрн", "мкр", "мікрорайон", "микр", "микр.", "микрорайон", "м-н",
    # VILLAGE
    "пос", "пос.", "смт", "смт.", "с.м.т", "пгт", "п г т", "пгт.", "село", "селище", "поселок", "с-ще",
    # STREET    
    "вул", "вул.", "вулиця", "ул", "ул.", "улица", "влу.", "в.", "вулю",
    "пров", "пров.", "провулок", "пер", "пер.", "переулок", "прос", "провул", "прв.",
    "бул", "бул.", "б-р", "бр", "бр.", "бур", "бур.", "бульвар", "бульв.",
    "просп", "просп.", "прт", "прт.", "прокт", "прокт.", "пр", "пр.", "п-т", "п-т.", "п-рт.", "проспект", "п-т", "пр-кт", "пр-к",
    "ж\м" , "масив", "массив", "житловий масив", "жилой массив", "ж.м.",
    "ш.", "шосе", "шоссе",
    "алея", "аллея",
    "майд" ,"майд.", "майдан",
    "розвилка", "развилка",
    "узвіз", "спуск",
    "проїзд", "проезд",
    "дорога",
    "наб", "наб.", "набер.", "набережна", "набережная",
    "парк",
    "сквер",
    "тупик",
    "прохід", "проход",
    "ст", "ст.", "станція", "станция",
    "остр", "остр.", "острів", "остров",
    "шлях", "путь",
    "гай", "роща", 
    "пл", "пл.", "площа", "площадь",
    "в'їзд", "въезд",
    "лінія", "линия",
    "траса", "трасса",
    "урочище",
    "шахта",
    "хутір", "хутор",
    "роз'їзд", "разъезд",
    "квартал",
    # HOUSING
    "корп.", "корп", "корпус",
    # HOSTEL
    "гурт", "гурт.", "гуртожиток", "общ", "общ.", "общежитие",
    # HOUSE
    "буд.", "будинок", "дом", "д.", "б.",
    # APARTMENT
    "кв.", "квартира",
    # ROOM
    "прим.",
    # SECTION
    "секція"

}

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
    address_string = unMergeType(address_string)

    tokens = re_tokens.findall(address_string)
  
    if not tokens:
        return []

    return tokens

def unMergeType(address):

    # Unmerge string, if exists housenumber + apartment type
    #
    if re.findall(r'\d{1,}[а-яА-ЯіІїЇґҐ]{1}[а-яА-ЯіІїЇґҐ]{1}\s', address):
        address = re.sub(r'(?<=\d)(?=[а-яА-ЯіІїЇґҐ]+\s)', ' ', address)

    if re.findall(r'кв\s\d+$', address):
        address = re.sub(r'(?=кв(?:\.|\.?)\s\d+)', ' ', address)
    
    if re.findall(r'(?<=\d[а-яА-ЯіІїЇґҐ]{1})(?=[а-яА-ЯіІїЇґҐ]\.\d\s)', address):
        address = re.sub(r'(?<=\d[а-яА-ЯіІїЇґҐ]{1})(?=[а-яА-ЯіІїЇґҐ]\.\d\s)', ' ', address)

    if re.findall(r'(?<=\d)(?=[а-яА-ЯіІїЇґҐ]{3,}(?:\s|\.\d+$))', address):
        address = re.sub(r'(?<=\d)(?=[а-яА-ЯіІїЇґҐ]{3,}(?:\s|\.\d+$))', ' ', address)

    if re.findall(r'\d+[а-яА-ЯіІїЇґҐ]\.\d+', address):
        address = re.sub(r'(?<=\d)(?=[а-яА-ЯіІїЇґҐ]\.\d+)', ' ', address)

    if re.findall(r'(?<=[а-яА-ЯіІїЇґҐ]\.)(?=\d+(?:\s|\,))', address):
        address = re.sub(r'(?<=[а-яА-ЯіІїЇґҐ]\.)(?=\d+(?:\s|\,))', ' ', address)

    if re.findall(r'[а-яА-ЯіІїЇґҐ]{1,}\s[а-яА-ЯіІїЇґҐ]{1,}\d\s', address):
        address = re.sub(r'(?<=[а-яА-ЯіІїЇґҐ])(?=\d\s)', ' ', address)

    if re.findall(r'(?<=\d{5})', address):
        address = re.sub(r'(?<=\d{5})', ' ', address)

    if re.findall(r'\.(?!\s)', address):
        address = re.sub(r'\.(?!\s)', '. ', address)

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
 
    REPO_URL = 'https://github.com/martinjack/uaddress/issues/new'
    DOCS_URL = ''
