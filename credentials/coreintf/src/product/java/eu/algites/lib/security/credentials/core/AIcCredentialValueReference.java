package eu.algites.lib.security.credentials.core;

import java.util.Objects;

/**
 * Immutable credential-document value reference.
 */
public final class AIcCredentialValueReference {
    private final AInCredentialValueSource source;
    private final String value;

    public AIcCredentialValueReference(AInCredentialValueSource aSource, String aValue) {
        source = Objects.requireNonNull(aSource, "Credential value source must not be null.");
        value = Objects.requireNonNull(aValue, "Credential value reference must not be null.");
        if (value.isEmpty()) {
            throw new IllegalArgumentException("Credential value reference must not be empty.");
        }
    }

    public AInCredentialValueSource getSource() {
        return source;
    }

    public String getValue() {
        return value;
    }
}
