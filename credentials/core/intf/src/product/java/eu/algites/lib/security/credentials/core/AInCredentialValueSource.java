package eu.algites.lib.security.credentials.core;

/**
 * Closed set of algorithms for resolving a credential field value.
 */
public enum AInCredentialValueSource {
    DIRECT_VALUE("direct_value"),
    FILE_CONTENT("file_content"),
    SECRET_CONTENT("secret_content"),
    ENVIRONMENT_VARIABLE_CONTENT("environment_variable_content");

    private final String id;

    AInCredentialValueSource(String aId) {
        id = aId;
    }

    public String getId() {
        return id;
    }

    /**
     * Returns the named alternative that represents this source in JSON/YAML
     * ValueSource choice objects. XML retains its Source and Value elements.
     *
     * @return the stable, case-sensitive property name for this source
     */
    public String getChoiceVariant() {
        return switch (this) {
            case DIRECT_VALUE -> "DirectValue";
            case FILE_CONTENT -> "FileContent";
            case SECRET_CONTENT -> "SecretContent";
            case ENVIRONMENT_VARIABLE_CONTENT -> "EnvironmentVariableContent";
        };
    }

    public static AInCredentialValueSource fromId(String aId) {
        if (aId == null) {
            throw new IllegalArgumentException("Credential value source must not be null.");
        }
        String locId = aId.trim();
        for (AInCredentialValueSource locSource : values()) {
            if (locSource.id.equals(locId)) {
                return locSource;
            }
        }
        throw new IllegalArgumentException("Unsupported credential value source: " + aId);
    }
}
