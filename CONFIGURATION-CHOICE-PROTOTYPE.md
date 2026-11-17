# Prototype: Configuration typed map with named choices (schema-only)

**Status: experimental — NOT ready for `devops/bootstrap/bootstrap.sh --prepare-only`.**
This is a schema-only design experiment from the r17 baseline. No changes were
made to Defs/SDO Codegen, handwritten Credential API, or generated Java/Python
sources. Do not publish as an API release until the generator and runtime
semantics below have been resolved and compiled together.

## Source format correspondence

The JSONDEFS and YAMLDEFS `credential-profiles_1` schemas now use a named
`$defs/ConfigurationValueType` with both standard `oneOf` and explicit
`x-algites-defscodegen-choice: true` with alternatives declared in sibling `properties`. The three alternatives are named
`StringVariant`, `IntegerVariant`, `BooleanVariant`, each wrapping exactly one
required property (`StringValue`, `IntegerValue`, `BooleanValue`). The
`Configuration` object uses `additionalProperties` referencing the choice.

```json
{
  "development": {
    "Configuration": {
      "server": { "StringValue": "localhost" },
      "timeout": { "IntegerValue": 30 },
      "enabled": { "BooleanValue": true }
    }
  }
}
```

The XSD uses the same three named variants and a named complex choice type
`ConfigurationValueType`. The per-entry XML key is the required `Name` attribute;
`ConfigurationEntryType` extends the choice type with the key attribute.
An `xs:key` on the enclosing `Configuration` element enforces uniqueness.

```xml
<CredentialProfiles xmlns="https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/security/credentials/core/credential-profiles_1.xsd">
  <Profile Id="development">
    <Configuration>
      <Entry Name="server"><StringValue>localhost</StringValue></Entry>
      <Entry Name="timeout"><IntegerValue>30</IntegerValue></Entry>
      <Entry Name="enabled"><BooleanValue>true</BooleanValue></Entry>
    </Configuration>
  </Profile>
</CredentialProfiles>
```

The aim is a logical `Map<String, ConfigurationValueType>`; the XML entry type
is a *serialization adapter*, not another logical value type. The XSD does not
have an `additionalProperties` keyword, so that mapping requires explicit,
generic Codegen semantics rather than a name-based special case.

`xs:integer` and JSON `integer` have arbitrary mathematical precision; a
Java mapping to `BigInteger` is lossless, while a plain 64-bit `Long` would
require a bounded JSON schema (minimum/maximum) and `xs:long`.

## What was verified

- The three source schemas validate at the schema-definition level: XSD 1.0
  via `lxml.etree.XMLSchema`, JSON Schema draft 2020-12 via `jsonschema`.
- Both forms accept corresponding valid choice instances and reject wrong
  value types, multiple choice branches, and (for XML) duplicate `Name` keys.
- `python -m pytest -q credentials/core/intf/src/develop/python/test_configuration_choice_schema.py`
  -> **3 passed** (tested locally with `pytest`, `lxml`, `jsonschema`).

## What Codegen currently does *not* support

With this clean XSD design, the unchanged r17 Python Defs Codegen fails on

```text
Unresolved or ambiguous xs:key field step '@Name' in '@Name'
```

because the `xs:key` field resolver looks only for direct attributes of an
entry type, not attributes introduced by a `complexContent/extension`.

If the `xs:key` is temporarily omitted in a test-only copy, it instead fails:

```text
XML extension requires object contracts
```

because `ConfigurationEntryType` extends a *named choice* and the generator
currently only handles object-contract bases for XML complex extensions.

A separate throwaway experiment changed `ConfigurationEntryType` to have a
**direct** `xs:choice` alongside its `Name` attribute (without inheritance).
Defs generated 264 representations, but did **not** generate equivalent API:

- `AIigCredentialProfile_1.getConfiguration()` returned
  `AIiMultiMappedList<AIigConfigurationValueType_1>`.
- `AIig_jCredentialProfile_1` and `AIig_yCredentialProfile_1` returned
  `AIiMultiMappedList<AIigCredentialProfileConfigurationAdditionalProperties_1>`;
  these Java generic signatures clash with the common parent.
- The XML entry's direct `xs:choice` was flattened into three separate
  fields/getters, each incorrectly marked `REQUIRED`. A choice requires exactly
  one branch, *not all three simultaneously*.
- The XML `getConfiguration()` path still returned its XML-specific
  `AIig_xConfigurationType_1`, not a shared logical map.

Consequently, **successful Defs source generation is not enough** to establish
cross-format equivalence, and the direct-choice workaround was NOT retained.

## Proposed changes requiring discussion before editing Codegen

1. Resolve XML `xs:key` paths against inherited attributes and elements,
   including `complexContent/extension`, without hard-coding `Name` or `Entry`.
2. Permit an XML complex type to extend a named `xs:choice` with a required
   key attribute, preserving the value choice in the projected DataObject.
3. Distinguish logical map value type `V` from the *serialization item* type
   `Entry<K,V>` for JSON/YAML `additionalProperties` and XML keyed children.
   Ensure all specialized Java/Python getters satisfy the common contract.
4. Validate choice cardinality: no generated API may interpret `xs:choice`
   as all required fields.
5. Add regression tests for these cross-format cases, SDO Java and Python
   generation, compile checks and runtime round-trips.

**API note:** this experiment intentionally changes configurations from
`String -> String` to `String -> tagged choice`; the handwritten
`AIcCredentialProfile.getConfiguration(): Map<String,String>` API is unchanged.
Agree the desired public API and migration policy before publishing the change.

## r19 vocabulary migration

The JSONDEFS/YAMLDEFS ConfigurationValueType is now an object whose three
scalar alternatives are declared in `properties`: StringValue, IntegerValue
and BooleanValue. It has standard `minProperties: 1`, `maxProperties: 1` and
`additionalProperties: false`, so off-the-shelf Draft 2020-12 validators
enforce exactly one variant. The XML XSD remains a standard `xs:choice`.

The Defs Codegen source readers now recognize the boolean marker, but the
original prototype still has unresolved XML inheritance and cross-format map
projection issues. It is not yet proven bootstrap-buildable.
