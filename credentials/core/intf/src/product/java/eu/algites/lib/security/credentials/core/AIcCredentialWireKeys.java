package eu.algites.lib.security.credentials.core;

/**
 * Canonical wire-level property names of the credential document format.
 *
 * <p>These constants are stable across Defs Codegen output and independent of
 * generated Java interface naming. They are external representation names,
 * not SmartDataObject semantic field identities or naming conventions.
 */
public final class AIcCredentialWireKeys {
    /** Property selecting the source from which a credential value is resolved. */
    public static final String SOURCE = "Source";

    /** Property carrying the content or reference of a credential value. */
    public static final String VALUE = "Value";

    /** Optional JSON/YAML root schema location hint, not a credential profile. */
    public static final String SCHEMA_HINT = "$schema";

    /** Prevents instances of this wire-format constant namespace. */
    private AIcCredentialWireKeys() {
    }
}
