# -*- coding: utf-8 -*-
import logging
from difflib import SequenceMatcher


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s.%(lineno)d  - %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def is_english(s):
    try:
        s.encode('ascii')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    else:
        return True


def get_field_mapping(config, section, table_name):
    field_mapping = {}
    attr_dict = dict(config.items(section))
    for attr in attr_dict:
        if table_name in attr and len(table_name.split('.')) == 3:
            if table_name.split('.')[1] not in field_mapping:
                field_mapping[table_name.split('.')[1]] = {}
            field_mapping[table_name.split('.')[1]][table_name.split('.')[2]] = attr_dict[attr]
