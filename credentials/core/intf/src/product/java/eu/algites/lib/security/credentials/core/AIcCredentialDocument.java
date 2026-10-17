package eu.algites.lib.security.credentials.core;

import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Parsed universal Algites credential document containing any number of named credential profiles.
 */
public final class AIcCredentialDocument {
    private static final Pattern PROFILE_ID_PATTERN = Pattern.compile("^[a-z0-9]+(?:-[a-z0-9]+)*$");

    private final Map<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> profiles;

    public AIcCredentialDocument(
        Map<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> aProfiles
    ) {
        Objects.requireNonNull(aProfiles, "Credential profiles must not be null.");
        LinkedHashMap<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> locProfiles =
            new LinkedHashMap<>();
        aProfiles.forEach((locProfileId, locTypedCredentials) -> {
            Objects.requireNonNull(locProfileId, "Credential profile id must not be null.");
            if (!PROFILE_ID_PATTERN.matcher(locProfileId).matches()) {
                throw new IllegalArgumentException(
                    "Credential profile id must use canonical lowercase dash-separated form: " + locProfileId
                );
            }
            Objects.requireNonNull(locTypedCredentials, "Credential profile values must not be null.");
            EnumMap<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>> locTypes =
                new EnumMap<>(AInCredentialType.class);
            locTypedCredentials.forEach((locType, locFields) -> {
                Objects.requireNonNull(locType, "Credential type must not be null.");
                Objects.requireNonNull(locFields, "Credential fields must not be null.");
                EnumMap<AInCredentialField, AIcCredentialValueReference> locFieldCopy =
                    new EnumMap<>(AInCredentialField.class);
                locFields.forEach((locField, locReference) -> {
                    Objects.requireNonNull(locField, "Credential field must not be null.");
                    Objects.requireNonNull(locReference, "Credential value reference must not be null.");
                    if (!locType.getSupportedFields().contains(locField)) {
                        throw new IllegalArgumentException(
                            "Credential field '" + locField.getId() + "' is not supported by credential type '" +
                                locType.getId() + "'."
                        );
                    }
                    locFieldCopy.put(locField, locReference);
                });
                for (AInCredentialField locRequiredField : locType.getRequiredFields()) {
                    if (!locFieldCopy.containsKey(locRequiredField)) {
                        throw new IllegalArgumentException(
                            "Credential profile '" + locProfileId + "' type '" + locType.getId() +
                                "' is missing required field '" + locRequiredField.getId() + "'."
                        );
                    }
                }
                locTypes.put(locType, Collections.unmodifiableMap(locFieldCopy));
            });
            if (locTypes.isEmpty()) {
                throw new IllegalArgumentException("Credential profile '" + locProfileId + "' must define at least one type.");
            }
            locProfiles.put(locProfileId, Collections.unmodifiableMap(locTypes));
        });
        profiles = Collections.unmodifiableMap(locProfiles);
    }

    public Set<String> getProfileIds() {
        return profiles.keySet();
    }

    public boolean containsProfile(String aProfileId) {
        return profiles.containsKey(Objects.requireNonNull(aProfileId, "Credential profile id must not be null."));
    }

    public Optional<Map<AInCredentialField, AIcCredentialValueReference>> getCredentialValues(
        String aProfileId,
        AInCredentialType aType
    ) {
        Objects.requireNonNull(aProfileId, "Credential profile id must not be null.");
        Objects.requireNonNull(aType, "Credential type must not be null.");
        Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>> locProfile = profiles.get(aProfileId);
        return locProfile == null ? Optional.empty() : Optional.ofNullable(locProfile.get(aType));
    }

    public Map<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> getProfiles() {
        return profiles;
    }
}
