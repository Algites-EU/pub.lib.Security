package eu.algites.lib.security.credentials.core.impl.standard;


import eu.algites.lib.security.credentials.core.AIcCredentialDocument;
import eu.algites.lib.security.credentials.core.AInCredentialField;
import eu.algites.lib.security.credentials.core.AInCredentialType;
import eu.algites.lib.security.credentials.core.AInCredentialValueSource;
import eu.algites.lib.security.credentials.core.AIxCredentialException;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.ByteArrayInputStream;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public final class AItcCredentialDocumentReaderTest {
    private static final String JSON_DOCUMENT =
        "{\"profile\":{\"Basic\":{\"Username\":{\"Source\":\"direct_value\",\"Value\":\"user\"}," +
            "\"Password\":{\"Source\":\"direct_value\",\"Value\":\"password\"}}}}";

    private static final String YAML_DOCUMENT =
        "profile:\n" +
            "  Basic:\n" +
            "    Username:\n" +
            "      Source: direct_value\n" +
            "      Value: user\n" +
            "    Password:\n" +
            "      Source: direct_value\n" +
            "      Value: password\n";

    private static final String XML_DOCUMENT =
        "<CredentialDocument>" +
            "<Profile Id=\"profile\">" +
            "<Basic>" +
            "<Username><Source>direct_value</Source><Value>user</Value></Username>" +
            "<Password><Source>direct_value</Source><Value>password</Value></Password>" +
            "</Basic>" +
            "</Profile>" +
            "</CredentialDocument>";

    @Test
    public void testDetectsJsonYamlAndXml() {
        AIcCredentialDocumentReader locReader = new AIcCredentialDocumentReader();
        assertBasic(locReader.read(JSON_DOCUMENT));
        assertBasic(locReader.read(YAML_DOCUMENT));
        assertBasic(locReader.read(XML_DOCUMENT));
    }

    @Test
    public void testDetectionPreservesNonResettableInputStream() {
        byte[] locBytes = JSON_DOCUMENT.getBytes(StandardCharsets.UTF_8);
        InputStream locInput = new FilterInputStream(new ByteArrayInputStream(locBytes)) {
            @Override
            public boolean markSupported() {
                return false;
            }

            @Override
            public synchronized void mark(int aReadLimit) {
            }

            @Override
            public synchronized void reset() throws IOException {
                throw new IOException("reset is not supported");
            }
        };
        assertBasic(new AIcCredentialDocumentReader().read(locInput));
    }

    @Test
    public void testExplicitReaders() {
        AIcCredentialDocumentReader locReader = new AIcCredentialDocumentReader();
        assertBasic(locReader.readJson(JSON_DOCUMENT));
        assertBasic(locReader.readYaml(YAML_DOCUMENT));
        assertBasic(locReader.readXml(XML_DOCUMENT));
    }

    @Test
    public void testRootSchemaHintIsNotACredentialProfile() {
        AIcCredentialDocumentReader locReader = new AIcCredentialDocumentReader();
        String locSchemaUri = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/lib/security/credentials/core/credential-document_1.yamldef.schema.json";
        AIcCredentialDocument locJsonDocument = locReader.readJson(
            "{\"$schema\":\"" + locSchemaUri + "\"," + JSON_DOCUMENT.substring(1));
        AIcCredentialDocument locYamlDocument = locReader.readYaml("$schema: " + locSchemaUri + "\n" + YAML_DOCUMENT);
        assertBasic(locJsonDocument);
        assertBasic(locYamlDocument);
        Assert.assertFalse(locJsonDocument.containsProfile("$schema"));
        Assert.assertFalse(locYamlDocument.containsProfile("$schema"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readJson("{\"$schema\":4}"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readYaml("$schema: 4\n"));
    }


    /**
     * Ensures the one-of-four-but-distinct profile map is shared across the
     * JSON, YAML and XML forms, including rejecting an empty XML xs:all group.
     */
    @Test
    public void testRejectsEmptyProfileInAllFormats() {
        AIcCredentialDocumentReader locReader = new AIcCredentialDocumentReader();
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readJson("{\"profile\":{}}"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readYaml("profile: {}\n"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readXml(
            "<CredentialDocument><Profile Id=\"profile\"/></CredentialDocument>"));
    }

    /**
     * A duplicate credential type must fail in every input format instead of
     * silently overwriting its first occurrence during JSON/YAML parsing.
     */
    @Test
    public void testRejectsDuplicateCredentialTypeInAllFormats() {
        AIcCredentialDocumentReader locReader = new AIcCredentialDocumentReader();
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readJson(
            "{\"profile\":{\"Basic\":{},\"Basic\":{}}}"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readYaml(
            "profile:\n  Basic: {}\n  Basic: {}\n"));
        Assert.expectThrows(AIxCredentialException.class, () -> locReader.readXml(
            XML_DOCUMENT.replace("</Profile>", XML_DOCUMENT.substring(
                XML_DOCUMENT.indexOf("<Basic>"), XML_DOCUMENT.indexOf("</Basic>") + "</Basic>".length())
                + "</Profile>")));
    }

    private static void assertBasic(AIcCredentialDocument aDocument) {
        var locValues = aDocument.getCredentialValues("profile", AInCredentialType.BASIC).orElseThrow();
        Assert.assertEquals(locValues.get(AInCredentialField.USERNAME).getSource(), AInCredentialValueSource.DIRECT_VALUE);
        Assert.assertEquals(locValues.get(AInCredentialField.USERNAME).getValue(), "user");
        Assert.assertEquals(locValues.get(AInCredentialField.PASSWORD).getValue(), "password");
    }
}
