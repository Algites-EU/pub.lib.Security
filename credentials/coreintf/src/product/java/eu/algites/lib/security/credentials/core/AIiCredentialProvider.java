package eu.algites.lib.security.credentials.core;

import java.util.Optional;

/**
 * Resolves a complete credential profile from one runtime source.
 */
public interface AIiCredentialProvider {
    Optional<AIcCredential> resolve(AIcCredentialProfile aProfile);
}
