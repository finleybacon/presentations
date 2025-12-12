```bash {code-line-numbers="|5,6,7,8,9,10,11,12,13,14|28,29"}
(calm-demo) fbacon@CS00058225:~/GitHub/presentations/calm/architecture$ calm validate -p pattern.json -a bad-architecture.json
info [file-system-document-loader]:     bad-architecture.json exists, loading as file...
info [file-system-document-loader]:     pattern.json exists, loading as file...
info [calm-validate]:     Formatting output as json
{
    "jsonSchemaValidationOutputs": [
        {
            "code": "json-schema",
            "severity": "error",
            "message": "must be equal to constant",
            "path": "/relationships/0/relationship-type",
            "schemaPath": "#/properties/relationships/prefixItems/0/properties/relationship-type/const"
        }
    ],
    "spectralSchemaValidationOutputs": [
        {
            "code": "architecture-nodes-must-be-referenced",
            "severity": "warning",
            "message": "Node with ID 'trigger' is not referenced by any relationships.",
            "path": "/nodes/0/unique-id",
            "schemaPath": "",
            "line_start": 0,
            "line_end": 0,
            "character_start": 118,
            "character_end": 127
        }
    ],
    "hasErrors": true,
    "hasWarnings": true
```