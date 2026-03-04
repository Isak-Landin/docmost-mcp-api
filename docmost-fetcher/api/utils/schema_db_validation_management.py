import json
from uuid import UUID
import uuid
from datetime import datetime
from collections import deque
import logging
import os
from typing import Any



from errors import INVALID_INPUT, NOT_FOUND, DB_ERROR, UNEXPECTED_ERROR, ok, err

logger = logging.getLogger(__name__)

def dict_depth(d, depth=0):
    if not isinstance(d, dict) or not d:
        return depth
    return max(dict_depth(v, depth+1) for k, v in d.items())

# ---------------------------------------------- #
# ------ PAGES QUERY REFACTOR FUNCTIONS -------- #
# ---------------------------------------------- #

# This function is intended to be used by page content db query functions to reformat content -
#  by removing extra "+" and "\n".
def refactor_content(_text_content):
    _last_char_list = []
    _reformated_text = ""
    for char in _text_content:
        should_append = True
        try:
            if len(_last_char_list) >= 2:
                if char == "+" and _last_char_list[-1] == "+" and _last_char_list[-2] == "+":
                    should_append = False
                elif char == "\n" and _last_char_list[-1] == "\n":
                    should_append = False
            if should_append:
                _reformated_text += char

            _last_char_list.append(char)
        except IndexError as e:
            logger.warning("Index error when refactoring text content: ", e)
            print("IndexError: ", e)
            continue
        except Exception as e:
            logger.warning(f"An Error occurred during runtime " + f"str(e)")
            print("Other error when refactoring text content: ", e)
            continue

    return _reformated_text


# ------------------------------------------------------------ #
# ------ VALIDATE FOR QUERY OUTPUT VS SCHEMAS FUNCTIONS ------ #
# ------------------------------------------------------------ #
def _validate_against_schema(refactored_envelope: dict, schema_sot: dict):
    """
    Validates that `data` matches the structural type mapping of `schema`.
    Uses convert_schema_to_key_value_relation_list().
    """

    if not isinstance(refactored_envelope, dict):
        return err(INVALID_INPUT, message="refactored_envelope must be a dict", value=str(refactored_envelope))

    schema_rel = recursive_relational_list_for_sot(schema_sot)

    if not isinstance(schema_rel, list):
        return err(UNEXPECTED_ERROR, message="During runtime, schema_rel list was not a list. This is a logical error", value=str(schema_rel))


is_levels_verified: list[bool] = []

def recursive_compare_sot_relation_to_envelope(_envelope: dict, _sot_relational_list: list):
    __depth_envelope = dict_depth(_envelope)
    __depth_sot = len(_sot_relational_list)

    if type(_envelope) != dict or type(_sot_relational_list) != list:
        return err(
            UNEXPECTED_ERROR,
            message="During runtime, envelope dict or sot relational list was not the correct type",
            value=f"Envelope: {_envelope}" + " " + f"Relational list: {_sot_relational_list}",
        )


    if __depth_envelope != __depth_sot:
        return err(
            UNEXPECTED_ERROR,
            message="The depth of envelope and sot did not match, this suggest internal logical inconsistency.",
            value=f"Envelope: {str(_envelope)}" + " " + f"Relational list: {str(_sot_relational_list)}",
        )

relational_list_envelope = []
def recursive_relational_list_envelope(_envelope: dict):
    """
    First two functions are used in the recursive creation. Since we have to convert some stringified values and keys
    in prod passed envelopes,

    @def convert_key_to_real_type():
        @__key, a key passed in its raw form

    @def convert_value_to_real_type():
        @__value, a value passed in its raw form
    """
    def convert_key_to_real_type(__key):
        envelope_key_types = {
            str: [uuid.UUID],
        }

        if not __key:
            return err(
                UNEXPECTED_ERROR,
                message="Key in dict cannot be None. During runtime when creating relation list for envelope, None key was found.",
                value=str(_envelope)
            )
        if type(__key) == str:
            for __type in envelope_key_types[str]:
                try:
                    __type(__key)
                    return __type
                except ValueError:
                    continue
            return str
        else:
            return type(__key)

    def convert_value_to_type(__value):
        envelope_value_types = {
            str: [uuid.UUID, datetime],
        }
        if not __value:
            return None
        if type(__value) == str:
            for __type in envelope_value_types[str]:
                try:
                    __type(__value)
                    return __type
                except ValueError:
                    continue
            return str
        else:
            return type(__value)

    """
    Normal recursive functionality begins here. The following contents aim to solve the building of the relational
    envelope list. The returned list will be used to later be compared with the sot_relational_list.
    
    @_envelope - is a parameter passed which corresponds to a prod retrieval of docmost db data, converted into SOT dict
    format. The format is defined in their corresponding schema files.
    """

    for k, v in _envelope.items():




relational_list_sot = []
def recursive_relational_list_sot(_sot: dict):
    def check_type(string_literal: str):
        dict_value_types = {
            uuid.UUID: "uuid",
            str: "string",
            datetime: "datetime",
            dict: "dict",
        }
        type_returned = None
        if not string_literal:
            return type_returned
        elif dict_value_types[uuid.UUID] in string_literal:
            type_returned = uuid.UUID
        elif dict_value_types[str] in string_literal:
            type_returned = str
        elif dict_value_types[datetime] in string_literal:
            type_returned = datetime
        else:
            pass
        return type_returned

    global relational_list_sot
    level_list = [[], []]
    for k, v in _sot.items():
        level_list[0].append(check_type(k))
        if isinstance(v, dict):
            level_list[1].append(dict)
        else:
            level_list[1].append(check_type(v))

    relational_list_sot.append(level_list)

    for v in _sot.values():
        if isinstance(v, dict):
            recursive_relational_list_for_sot(v)

    return relational_list_sot


# MODE
MODE = os.getenv("MODE", "dev")
if MODE == "prod":
    # SCHEMA FILES ENVS PROD
    #  Ensure base path contains trailing / always.
    SCHEMA_BASE_PATH = os.getenv("SCHEMA_BASE_PATH", "./schemas/")
else:
    SCHEMA_BASE_PATH = os.getenv("SCHEMA_BASE_PATH_DEV", "/home/isakadmin/docmost-ai-standalone-software/schemas/")


# SCHEMA ENVS INDEPENDENT OF PROD AND DEV
_SINGLE_PAGE_CONTENT_SCHEMA_FILE_NAME = os.getenv(
    "SINGLE_PAGE_CONTENT_SCHEMA_FILE", "single_page_content.json"
)
_SINGLE_PAGE_SCHEMA_FILE_NAME = os.getenv(
    "SINGLE_PAGE_SCHEMA_FILE", "single_page.json"
)
_SINGLE_SPACE_SCHEMA_FILE_NAME = os.getenv(
    "SINGLE_SPACE_SCHEMA_FILE", "single_space.json"
)

SINGLE_PAGE_CONTENT_SCHEMA_FILE_PATH = SCHEMA_BASE_PATH + _SINGLE_PAGE_CONTENT_SCHEMA_FILE_NAME
SINGLE_PAGE_SCHEMA_FILE_PATH = SCHEMA_BASE_PATH + _SINGLE_PAGE_SCHEMA_FILE_NAME
SINGLE_SPACE_SCHEMA_FILE_PATH = SCHEMA_BASE_PATH + _SINGLE_SPACE_SCHEMA_FILE_NAME

# DICTS FROM SCHEMA FILES
SINGLE_PAGE_CONTENT_SCHEMA_DICT = {}
SINGLE_PAGE_SCHEMA_DICT = {}
SINGLE_SPACE_SCHEMA_DICT = {}

for file in (SINGLE_PAGE_SCHEMA_FILE_PATH, SINGLE_PAGE_CONTENT_SCHEMA_FILE_PATH, SINGLE_SPACE_SCHEMA_FILE_PATH):
    with open(file, "r") as f:
        if _SINGLE_PAGE_CONTENT_SCHEMA_FILE_NAME in file:
            SINGLE_PAGE_CONTENT_SCHEMA_DICT = json.load(f)
        elif _SINGLE_PAGE_SCHEMA_FILE_NAME in file:
            _SINGLE_PAGE_SCHEMA_FILE_NAME = json.load(f)
        elif _SINGLE_SPACE_SCHEMA_FILE_NAME in file:
            SINGLE_SPACE_SCHEMA_DICT = json.load(f)


SCHEMAS = {
    "content_single": SINGLE_PAGE_CONTENT_SCHEMA_DICT,
    "content_multi": SINGLE_PAGE_CONTENT_SCHEMA_DICT,
    "page_single": SINGLE_PAGE_SCHEMA_DICT,
    "page_multi": SINGLE_PAGE_SCHEMA_DICT,
    "space_single": SINGLE_SPACE_SCHEMA_DICT,
    "space_multi": SINGLE_SPACE_SCHEMA_DICT,
}

allowed_types = (
    "content_single",
    "content_multi",
    "page_single",
    "page_multi",
    "space_single",
    "space_multi",
)

# ---------------------------------------------------------------------------------- #
# ------ EXPOSED FUNCTION TO BE USED TO VERIFY DICT BEFORE RETURNING RESPONSE ------ #
# ---------------------------------------------------------------------------------- #

def validate_dict(schema_to_check: dict, schema_type: str):
    if schema_type not in allowed_types:
        logger.warning(f"Invalid schema type {schema_type}")
        return False, {
            "ok": False,
            "error": "invalid_schema_type",
            "allowed": list(allowed_types),
        }

    schema = SCHEMAS.get(schema_type)
    if not isinstance(schema, dict):
        logger.critical(f"Schema missing or invalid for type={schema_type}")
        return False, {
            "ok": False,
            "error": "schema_missing",
            "value": schema_type,
        }

    return _validate_against_schema(schema_to_check, schema)