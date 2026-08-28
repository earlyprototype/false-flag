"""Structural DTDL v3 validator for the interop model set. Stdlib only.

Not the official DTDLParser (no .NET SDK on this machine): checks the
structural rules that matter for a legal model set - JSON well-formedness,
@context, DTMI grammar, @type rules, contents element types, schema
whitelist, Enum shape, Relationship target resolution - and nothing
semantic beyond them. Official-parser validation is a pending follow-up
(see README.md).

Usage:
    python interop/validate_dtdl.py [models_dir]

Exit 0 when every model file passes; prints one line per error otherwise.
"""

import json
import re
import sys
from pathlib import Path

# DTMI grammar per the DTDL spec (segments start with a letter, no trailing
# underscore; version 1-9 digits, no leading zero).
DTMI_RE = re.compile(
    r"^dtmi:[A-Za-z](?:[A-Za-z0-9_]*[A-Za-z0-9])?"
    r"(?::[A-Za-z](?:[A-Za-z0-9_]*[A-Za-z0-9])?)*;[1-9][0-9]{0,8}$"
)
NAME_RE = re.compile(r"^[A-Za-z](?:[A-Za-z0-9_]*[A-Za-z0-9])?$")

CONTEXT_V3 = "dtmi:dtdl:context;3"
PRIMITIVE_SCHEMAS = {
    "boolean", "date", "dateTime", "double", "duration",
    "float", "integer", "long", "string", "time",
}
CONTENT_TYPES = {"Property", "Telemetry", "Relationship", "Command", "Component"}
COMPLEX_TYPES = {"Array", "Enum", "Map", "Object"}

INTERFACE_KEYS = {
    "@context", "@id", "@type", "displayName", "description", "comment",
    "contents", "schemas", "extends",
}
ELEMENT_KEYS = {
    "Property": {"@type", "@id", "name", "schema", "displayName",
                 "description", "comment", "writable"},
    "Telemetry": {"@type", "@id", "name", "schema", "displayName",
                  "description", "comment"},
    "Relationship": {"@type", "@id", "name", "target", "displayName",
                     "description", "comment", "minMultiplicity",
                     "maxMultiplicity", "properties", "writable"},
}


class Validator:
    def __init__(self):
        self.errors = []
        self.interface_ids = {}   # dtmi -> file
        self.schema_ids = {}      # dtmi -> file
        self.docs = []            # (file, interface_dict)

    def err(self, where, message):
        self.errors.append(f"{where}: {message}")

    # -- pass 1: load files, collect ids --------------------------------

    def load(self, path):
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            self.err(path.name, f"unreadable or invalid JSON ({exc})")
            return
        docs = data if isinstance(data, list) else [data]
        for i, doc in enumerate(docs):
            where = f"{path.name}[{i}]"
            if not isinstance(doc, dict):
                self.err(where, "top-level entry is not a JSON object")
                continue
            self._register(where, doc)
            self.docs.append((where, doc))

    def _register(self, where, doc):
        dtmi = doc.get("@id")
        if not isinstance(dtmi, str) or not DTMI_RE.match(dtmi):
            self.err(where, f"missing or malformed interface @id: {dtmi!r}")
        elif len(dtmi) > 128:
            self.err(where, f"interface @id exceeds 128 chars: {dtmi}")
        elif dtmi in self.interface_ids:
            self.err(where, f"duplicate @id {dtmi}")
        else:
            self.interface_ids[dtmi] = where
        for schema in doc.get("schemas", []) or []:
            sid = schema.get("@id") if isinstance(schema, dict) else None
            if not isinstance(sid, str) or not DTMI_RE.match(sid):
                self.err(where, f"schemas entry missing/malformed @id: {sid!r}")
            elif sid in self.schema_ids or sid in self.interface_ids:
                self.err(where, f"duplicate schema @id {sid}")
            else:
                self.schema_ids[sid] = where

    # -- pass 2: validate each interface --------------------------------

    def check_interface(self, where, doc):
        ctx = doc.get("@context")
        ctx_list = ctx if isinstance(ctx, list) else [ctx]
        if CONTEXT_V3 not in ctx_list:
            self.err(where, f"@context must include {CONTEXT_V3!r}, got {ctx!r}")
        if doc.get("@type") != "Interface":
            self.err(where, f"top-level @type must be 'Interface', got {doc.get('@type')!r}")
        for key in doc:
            if key not in INTERFACE_KEYS:
                self.err(where, f"unexpected interface key {key!r}")

        extends = doc.get("extends")
        if extends is not None:
            for parent in extends if isinstance(extends, list) else [extends]:
                if parent not in self.interface_ids:
                    self.err(where, f"extends target {parent!r} not in model set")

        for schema in doc.get("schemas", []) or []:
            if isinstance(schema, dict):
                self.check_schema(f"{where}.schemas", schema, top_level=True)

        names = set()
        contents = doc.get("contents", [])
        if not isinstance(contents, list):
            self.err(where, "contents must be a list")
            return
        for element in contents:
            self.check_element(where, element, names)

    def check_element(self, where, element, names):
        if not isinstance(element, dict):
            self.err(where, "contents entry is not an object")
            return
        etype = element.get("@type")
        if etype not in CONTENT_TYPES:
            self.err(where, f"contents entry has invalid @type {etype!r}")
            return
        name = element.get("name")
        eloc = f"{where}.{name or '?'}"
        if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
            self.err(eloc, f"missing or invalid element name {name!r}")
        elif name in names:
            self.err(eloc, f"duplicate content name {name!r}")
        else:
            names.add(name)

        allowed = ELEMENT_KEYS.get(etype)
        if allowed is None:
            self.err(eloc, f"@type {etype} is legal DTDL but unsupported by this validator")
            return
        for key in element:
            if key not in allowed:
                self.err(eloc, f"unexpected key {key!r} on {etype}")

        if etype in ("Property", "Telemetry"):
            if "schema" not in element:
                self.err(eloc, f"{etype} requires a schema")
            else:
                self.check_schema(eloc, element["schema"])
        elif etype == "Relationship":
            self.check_relationship(eloc, element)

    def check_relationship(self, where, element):
        target = element.get("target")
        if target is not None and target not in self.interface_ids:
            self.err(where, f"relationship target {target!r} does not resolve "
                            "to an interface in the model set")
        if element.get("minMultiplicity") not in (None, 0):
            self.err(where, "minMultiplicity must be 0 when present")
        maxm = element.get("maxMultiplicity")
        if maxm is not None and (not isinstance(maxm, int) or maxm < 1):
            self.err(where, f"maxMultiplicity must be an integer >= 1, got {maxm!r}")
        for prop in element.get("properties", []) or []:
            self.check_element(where, prop, set())

    def check_schema(self, where, schema, top_level=False):
        if isinstance(schema, str):
            if schema in PRIMITIVE_SCHEMAS:
                return
            if DTMI_RE.match(schema):
                if schema not in self.schema_ids and schema not in self.interface_ids:
                    self.err(where, f"schema reference {schema!r} does not resolve")
                return
            self.err(where, f"schema {schema!r} is neither a whitelisted "
                            "primitive nor a resolvable DTMI")
            return
        if not isinstance(schema, dict):
            self.err(where, f"schema must be a string or object, got {type(schema).__name__}")
            return
        stype = schema.get("@type")
        if stype not in COMPLEX_TYPES:
            self.err(where, f"complex schema @type must be one of {sorted(COMPLEX_TYPES)}, got {stype!r}")
            return
        allowed = {"@type", "@id", "displayName", "description", "comment"}
        if stype == "Array":
            allowed |= {"elementSchema"}
            if "elementSchema" not in schema:
                self.err(where, "Array requires elementSchema")
            else:
                self.check_schema(f"{where}.Array", schema["elementSchema"])
        elif stype == "Enum":
            allowed |= {"valueSchema", "enumValues"}
            self.check_enum(where, schema)
        elif stype == "Map":
            allowed |= {"mapKey", "mapValue"}
            self.check_map(where, schema)
        elif stype == "Object":
            allowed |= {"fields"}
            self.check_object(where, schema)
        for key in schema:
            if key not in allowed:
                self.err(where, f"unexpected key {key!r} on {stype}")
        if not top_level and "@id" in schema:
            sid = schema["@id"]
            if not isinstance(sid, str) or not DTMI_RE.match(sid):
                self.err(where, f"malformed schema @id {sid!r}")

    def check_enum(self, where, schema):
        value_schema = schema.get("valueSchema")
        if value_schema not in ("integer", "string"):
            self.err(where, f"Enum valueSchema must be 'integer' or 'string', got {value_schema!r}")
        values = schema.get("enumValues")
        if not isinstance(values, list) or not values:
            self.err(where, "Enum requires a non-empty enumValues list")
            return
        seen_names, seen_values = set(), set()
        for ev in values:
            if not isinstance(ev, dict):
                self.err(where, "enumValues entry is not an object")
                continue
            name = ev.get("name")
            if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
                self.err(where, f"invalid enum value name {name!r}")
            elif name in seen_names:
                self.err(where, f"duplicate enum value name {name!r}")
            else:
                seen_names.add(name)
            value = ev.get("enumValue")
            expected = str if value_schema == "string" else int
            if not isinstance(value, expected) or isinstance(value, bool):
                self.err(where, f"enumValue {value!r} does not match valueSchema {value_schema!r}")
            elif value in seen_values:
                self.err(where, f"duplicate enumValue {value!r}")
            else:
                seen_values.add(value)
            for key in ev:
                if key not in {"name", "enumValue", "displayName", "description", "comment", "@id"}:
                    self.err(where, f"unexpected key {key!r} on enum value")

    def check_map(self, where, schema):
        map_key = schema.get("mapKey")
        if not isinstance(map_key, dict) or map_key.get("schema") != "string" \
                or not NAME_RE.match(str(map_key.get("name", ""))):
            self.err(where, f"Map mapKey must be {{name, schema:'string'}}, got {map_key!r}")
        map_value = schema.get("mapValue")
        if not isinstance(map_value, dict) or "schema" not in map_value \
                or not NAME_RE.match(str(map_value.get("name", ""))):
            self.err(where, f"Map mapValue must be {{name, schema}}, got {type(map_value).__name__}")
        else:
            self.check_schema(f"{where}.mapValue", map_value["schema"])

    def check_object(self, where, schema):
        fields = schema.get("fields")
        if not isinstance(fields, list) or not fields:
            self.err(where, "Object requires a non-empty fields list")
            return
        seen = set()
        for field in fields:
            if not isinstance(field, dict):
                self.err(where, "Object field is not an object")
                continue
            name = field.get("name")
            if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > 64:
                self.err(where, f"invalid Object field name {name!r}")
            elif name in seen:
                self.err(where, f"duplicate Object field name {name!r}")
            else:
                seen.add(name)
            if "schema" not in field:
                self.err(f"{where}.{name}", "Object field requires a schema")
            else:
                self.check_schema(f"{where}.{name}", field["schema"])
            for key in field:
                if key not in {"name", "schema", "displayName", "description", "comment", "@id"}:
                    self.err(f"{where}.{name}", f"unexpected key {key!r} on Object field")


def validate_models(models_dir):
    """Validate every .json file in models_dir. Returns a list of error strings."""
    validator = Validator()
    paths = sorted(Path(models_dir).glob("*.json"))
    if not paths:
        validator.err(str(models_dir), "no .json model files found")
        return validator.errors, 0
    for path in paths:
        validator.load(path)
    for where, doc in validator.docs:
        validator.check_interface(where, doc)
    return validator.errors, len(validator.docs)


def main():
    models_dir = Path(sys.argv[1]) if len(sys.argv) > 1 \
        else Path(__file__).parent / "models"
    errors, count = validate_models(models_dir)
    if errors:
        for line in errors:
            print(f"ERROR {line}")
        print(f"FAIL: {len(errors)} error(s) across {count} interface(s)")
        return 1
    print(f"OK: {count} interfaces validated structurally clean ({models_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
