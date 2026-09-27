package eu.algites.lib.security.credentials.core;

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

    private static void assertBasic(AIcCredentialDocument aDocument) {
        var locValues = aDocument.getCredentialValues("profile", AInCredentialType.BASIC).orElseThrow();
        Assert.assertEquals(locValues.get(AInCredentialField.USERNAME).getSource(), AInCredentialValueSource.DIRECT_VALUE);
        Assert.assertEquals(locValues.get(AInCredentialField.USERNAME).getValue(), "user");
        Assert.assertEquals(locValues.get(AInCredentialField.PASSWORD).getValue(), "password");
    }
}
