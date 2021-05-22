import boto3
from pathlib import Path
from settings import settings
from datetime import datetime
import json
import spacy
from spacy.pipeline import EntityRuler
from spacy.matcher import Matcher
import re
from cachetools import LRUCache, cached

from utils import data_utils, dawa

cache = LRUCache(maxsize=4)


@cached(cache=cache)
def address_patterns():
    # Create the matcher and match on Token.lower if case-insensitive
    region_names, city_names, postalcode_names, postal_codes, street_names = dawa.get_address_data()
    region_patterns = [{"label": "REG", "pattern": region_name} for region_name in region_names]
    city_patterns = [{"label": "CITY", "pattern": city_name} for city_name in city_names]
    postalcodename_patterns = [{"label": "ZIPN", "pattern": postalcode_name} for postalcode_name in postalcode_names]
    postalcode_patterns = [{"label": "ZIP", "pattern": postal_code} for postal_code in postal_codes]
    streetname_patterns = [{"label": "STREET", "pattern": street_name} for street_name in street_names]
    return region_patterns, postalcodename_patterns, postalcode_patterns, city_patterns, streetname_patterns


class Anonymous:
    def __init__(self):
        self.spacy = self.load_spacy()

    def example_data(self):
        with open("data/dat.txt") as f:
            examples = f.readlines()
        return examples

    def load_spacy(self):
        nlp = spacy.load("da_core_news_sm")
        ruler = nlp.add_pipe("entity_ruler")
        for patterns in address_patterns():
            ruler.add_patterns(patterns)
        return nlp

    def address_matches(self, doc):
        street_nb_re = r"\d{1,3}[A-Z]?\s?[klthvs]{0,2}\d{0,3}\.?\s?[klthvs]{0,2}"
        patterns = [
            [{"ENT_TYPE": "STREET"}],
            [{"ENT_TYPE": "ZIPN"}],
            [{"ENT_TYPE": "CITY"}],
            [{"ENT_TYPE": "REG"}],
            [{"ENT_TYPE": "STREET"}, {"TEXT": {"REGEX": street_nb_re}}],
            [{"ENT_TYPE": "ZIPN"}, {"ENT_TYPE": "ZIP"}],
            [{"ENT_TYPE": "ZIP"}, {"ENT_TYPE": "ZIPN"}],
        ]
        matcher = Matcher(self.spacy.vocab)
        matcher.add("ADDR", patterns)
        matches = matcher(doc, as_spans=True)
        matches = spacy.util.filter_spans(matches)  # take longest when overlap
        return matches

    def preprocess_text(self, text: str):
        text = text.encode("latin-1").decode("unicode_escape")
        text = text.replace("\r", "\r ")
        text = text.replace("\n", "\n ")
        return text

    def postprocess_text(self, text: str):
        text = text.replace("\r ", "\r")
        text = text.replace("\n ", "\n")
        return text

    def anonymize(self, text: str):
        text = self.preprocess_text(text)
        doc = self.spacy(text)
        redacted_text = text
        ## redact named entities
        for ent in reversed(doc.ents):
            if ent.label_ == "PER":
                redacted_text = redacted_text[: ent.start_char] + f"<PERSON>" + redacted_text[ent.end_char :]
            if ent.label_ == "NORP":
                redacted_text = redacted_text[: ent.start_char] + f"<SENSITIVE>" + redacted_text[ent.end_char :]
            if ent.label_ == "GPE":
                redacted_text = redacted_text[: ent.start_char] + f"<NAMED_AREA>" + redacted_text[ent.end_char :]
            if ent.label_ == "LOC":
                redacted_text = redacted_text[: ent.start_char] + f"<LOCATION>" + redacted_text[ent.end_char :]
            if ent.label_ == "ORG":
                redacted_text = redacted_text[: ent.start_char] + f"<ORGANISATION>" + redacted_text[ent.end_char :]

        ## redact emails
        email_re = re.compile(r"\S+@\S+")
        redacted_text = email_re.sub("<EMAIL_ADDRESS>", redacted_text)

        ## redact telephone numbers
        phone_re = re.compile(r"(?:[+]\d{1,3}\s?)?(?:\d{3,5}\s?)(?:\d{3,5})")
        redacted_text = phone_re.sub("<PHONE_NUMBER>", redacted_text)

        doc = self.spacy(redacted_text)
        matches = self.address_matches(doc)
        for span in reversed(matches):
            redacted_text = redacted_text[: span.start_char] + f"<ADDRESS>" + redacted_text[span.end_char :]

        redacted_text = self.postprocess_text(redacted_text)
        return redacted_text


if __name__ == "__main__":
    anom = Anonymous()
    self = anom
    examples = anom.example_data()
    text = examples[0]
    redacted_text = self.anonymize(text)