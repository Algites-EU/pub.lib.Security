package eu.algites.lib.security.credentials.core;
import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;

import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;

import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;

import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;

import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;

import eu.algites.lib.security.credentials.core.AIigCredentialValueSourceFields_1;
import eu.algites.lib.security.credentials.core.AIigCredentials_1;


import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.BufferedInputStream;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Reads complete Algites credential documents from JSON, YAML, or XML.
 */
public final class AIcCredentialDocumentReader {
    private static final int DETECTION_PREFIX_SIZE = 8192;
    private static final ObjectMapper JSON_MAPPER = new ObjectMapper();
    private static final ObjectMapper YAML_MAPPER = new ObjectMapper(new YAMLFactory());

    public AIcCredentialDocument read(String aDocument) {
        Objects.requireNonNull(aDocument, "Credential document must not be null.");
        return read(new ByteArrayInputStream(aDocument.getBytes(StandardCharsets.UTF_8)));
    }

    public AIcCredentialDocument read(Path aPath) {
        Objects.requireNonNull(aPath, "Credential document path must not be null.");
        try (InputStream locInput = Files.newInputStream(aPath)) {
            return read(locInput);
        } catch (IOException aException) {
            throw new AIxCredentialException("Cannot read credential document from path '" + aPath + "'.", aException);
        }
    }

    public AIcCredentialDocument read(URL aUrl) {
        Objects.requireNonNull(aUrl, "Credential document URL must not be null.");
        try (InputStream locInput = aUrl.openStream()) {
            return read(locInput);
        } catch (IOException aException) {
            throw new AIxCredentialException("Cannot read credential document from URL '" + aUrl + "'.", aException);
        }
    }

    public AIcCredentialDocument read(InputStream aInput) {
        Objects.requireNonNull(aInput, "Credential document input stream must not be null.");
        BufferedInputStream locInput = aInput instanceof BufferedInputStream
            ? (BufferedInputStream) aInput
            : new BufferedInputStream(aInput, DETECTION_PREFIX_SIZE);
        AInCredentialDocumentFormat locFormat = detectFormat(locInput);
        return read(locInput, locFormat);
    }

    public AIcCredentialDocument readJson(String aDocument) {
        return readUtf8(aDocument, AInCredentialDocumentFormat.JSON);
    }

    public AIcCredentialDocument readYaml(String aDocument) {
        return readUtf8(aDocument, AInCredentialDocumentFormat.YAML);
    }

    public AIcCredentialDocument readXml(String aDocument) {
        return readUtf8(aDocument, AInCredentialDocumentFormat.XML);
    }

    public AIcCredentialDocument readJson(Path aPath) {
        return readPath(aPath, AInCredentialDocumentFormat.JSON);
    }

    public AIcCredentialDocument readYaml(Path aPath) {
        return readPath(aPath, AInCredentialDocumentFormat.YAML);
    }

    public AIcCredentialDocument readXml(Path aPath) {
        return readPath(aPath, AInCredentialDocumentFormat.XML);
    }

    public AIcCredentialDocument readJson(URL aUrl) {
        return readUrl(aUrl, AInCredentialDocumentFormat.JSON);
    }

    public AIcCredentialDocument readYaml(URL aUrl) {
        return readUrl(aUrl, AInCredentialDocumentFormat.YAML);
    }

    public AIcCredentialDocument readXml(URL aUrl) {
        return readUrl(aUrl, AInCredentialDocumentFormat.XML);
    }

    public AIcCredentialDocument readJson(InputStream aInput) {
        return read(aInput, AInCredentialDocumentFormat.JSON);
    }

    public AIcCredentialDocument readYaml(InputStream aInput) {
        return read(aInput, AInCredentialDocumentFormat.YAML);
    }

    public AIcCredentialDocument readXml(InputStream aInput) {
        return read(aInput, AInCredentialDocumentFormat.XML);
    }

    public AIcCredentialDocument read(InputStream aInput, AInCredentialDocumentFormat aFormat) {
        Objects.requireNonNull(aInput, "Credential document input stream must not be null.");
        Objects.requireNonNull(aFormat, "Credential document format must not be null.");
        return switch (aFormat) {
            case JSON -> parseTree(aInput, JSON_MAPPER, "JSON");
            case YAML -> parseTree(aInput, YAML_MAPPER, "YAML");
            case XML -> parseXml(aInput);
        };
    }

    private AIcCredentialDocument readUtf8(String aDocument, AInCredentialDocumentFormat aFormat) {
        Objects.requireNonNull(aDocument, "Credential document must not be null.");
        return read(new ByteArrayInputStream(aDocument.getBytes(StandardCharsets.UTF_8)), aFormat);
    }

    private AIcCredentialDocument readPath(Path aPath, AInCredentialDocumentFormat aFormat) {
        Objects.requireNonNull(aPath, "Credential document path must not be null.");
        try (InputStream locInput = Files.newInputStream(aPath)) {
            return read(locInput, aFormat);
        } catch (IOException aException) {
            throw new AIxCredentialException("Cannot read credential document from path '" + aPath + "'.", aException);
        }
    }

    private AIcCredentialDocument readUrl(URL aUrl, AInCredentialDocumentFormat aFormat) {
        Objects.requireNonNull(aUrl, "Credential document URL must not be null.");
        try (InputStream locInput = aUrl.openStream()) {
            return read(locInput, aFormat);
        } catch (IOException aException) {
            throw new AIxCredentialException("Cannot read credential document from URL '" + aUrl + "'.", aException);
        }
    }

    private AIcCredentialDocument parseTree(InputStream aInput, ObjectMapper aMapper, String aFormatName) {
        try {
            JsonNode locRoot = aMapper.readTree(aInput);
            if (locRoot == null || !locRoot.isObject()) {
                throw new AIxCredentialException("Credential document must contain a " + aFormatName + " object at its root.");
            }
            return fromObjectNode(locRoot);
        } catch (IOException aException) {
            throw new AIxCredentialException("Credential document is not valid " + aFormatName + ".", aException);
        }
    }

    private AIcCredentialDocument fromObjectNode(JsonNode aRoot) {
        LinkedHashMap<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> locProfiles =
            new LinkedHashMap<>();
        Iterator<Map.Entry<String, JsonNode>> locProfileIterator = aRoot.fields();
        while (locProfileIterator.hasNext()) {
            Map.Entry<String, JsonNode> locProfileEntry = locProfileIterator.next();
            String locProfileId = locProfileEntry.getKey();
            JsonNode locProfileNode = locProfileEntry.getValue();
            if (AIigCredentials_1.SCHEMA_FIELD_NAME__SCHEMA.equals(locProfileId)) {
                if (!locProfileNode.isTextual()) {
                    throw new AIxCredentialException("Credential document '$schema' must be a string.");
                }
                continue;
            }
            if (!locProfileNode.isObject()) {
                throw new AIxCredentialException("Credential profile '" + locProfileId + "' must be an object.");
            }
            EnumMap<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>> locTypes =
                new EnumMap<>(AInCredentialType.class);
            Iterator<Map.Entry<String, JsonNode>> locTypeIterator = locProfileNode.fields();
            while (locTypeIterator.hasNext()) {
                Map.Entry<String, JsonNode> locTypeEntry = locTypeIterator.next();
                AInCredentialType locType = credentialTypeFromPropertyName(locTypeEntry.getKey());
                locTypes.put(locType, parseFieldObject(locProfileId, locType, locTypeEntry.getValue()));
            }
            locProfiles.put(locProfileId, locTypes);
        }
        try {
            return new AIcCredentialDocument(locProfiles);
        } catch (IllegalArgumentException aException) {
            throw new AIxCredentialException(aException.getMessage(), aException);
        }
    }

    private Map<AInCredentialField, AIcCredentialValueReference> parseFieldObject(
        String aProfileId,
        AInCredentialType aType,
        JsonNode aTypeNode
    ) {
        if (!aTypeNode.isObject()) {
            throw new AIxCredentialException(
                "Credential profile '" + aProfileId + "' type '" + aType.getId() + "' must be an object."
            );
        }
        EnumMap<AInCredentialField, AIcCredentialValueReference> locFields = new EnumMap<>(AInCredentialField.class);
        Iterator<Map.Entry<String, JsonNode>> locFieldIterator = aTypeNode.fields();
        while (locFieldIterator.hasNext()) {
            Map.Entry<String, JsonNode> locFieldEntry = locFieldIterator.next();
            AInCredentialField locField;
            try {
                locField = AInCredentialField.fromId(locFieldEntry.getKey());
            } catch (IllegalArgumentException aException) {
                throw new AIxCredentialException(
                    "Credential profile '" + aProfileId + "' type '" + aType.getId() +
                        "' contains unsupported field '" + locFieldEntry.getKey() + "'.",
                    aException
                );
            }
            if (!aType.getSupportedFields().contains(locField)) {
                throw new AIxCredentialException(
                    "Credential profile '" + aProfileId + "' type '" + aType.getId() +
                        "' does not support field '" + locField.getId() + "'."
                );
            }
            locFields.put(locField, parseValueReference(aProfileId, aType, locField, locFieldEntry.getValue()));
        }
        return locFields;
    }

    private AIcCredentialValueReference parseValueReference(
        String aProfileId,
        AInCredentialType aType,
        AInCredentialField aField,
        JsonNode aNode
    ) {
        if (!aNode.isObject()) {
            throw fieldError(aProfileId, aType, aField, "must be an object containing Source and Value.");
        }
        JsonNode locSourceNode = aNode.get(AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__SOURCE);
        JsonNode locValueNode = aNode.get(AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__VALUE);
        if (locSourceNode == null || !locSourceNode.isTextual()) {
            throw fieldError(aProfileId, aType, aField, "is missing string property 'Source'.");
        }
        if (locValueNode == null || !locValueNode.isTextual()) {
            throw fieldError(aProfileId, aType, aField, "is missing string property 'Value'.");
        }
        if (aNode.size() != 2) {
            throw fieldError(aProfileId, aType, aField, "contains unsupported properties.");
        }
        try {
            return new AIcCredentialValueReference(
                AInCredentialValueSource.fromId(locSourceNode.textValue()),
                locValueNode.textValue()
            );
        } catch (IllegalArgumentException aException) {
            throw fieldError(aProfileId, aType, aField, aException.getMessage());
        }
    }

    private AIcCredentialDocument parseXml(InputStream aInput) {
        try {
            DocumentBuilderFactory locFactory = DocumentBuilderFactory.newInstance();
            locFactory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            locFactory.setFeature("http://xml.org/sax/features/external-general-entities", false);
            locFactory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            locFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            locFactory.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            locFactory.setExpandEntityReferences(false);
            locFactory.setNamespaceAware(false);
            Document locDocument = locFactory.newDocumentBuilder().parse(aInput);
            Element locRoot = locDocument.getDocumentElement();
            if (locRoot == null || !"CredentialDocument".equals(locRoot.getTagName())) {
                throw new AIxCredentialException("XML credential document root element must be CredentialDocument.");
            }
            LinkedHashMap<String, Map<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>>> locProfiles =
                new LinkedHashMap<>();
            for (Element locProfileElement : childElements(locRoot)) {
                if (!"Profile".equals(locProfileElement.getTagName())) {
                    throw new AIxCredentialException(
                        "XML credential document contains unsupported element '" + locProfileElement.getTagName() + "'."
                    );
                }
                String locProfileId = locProfileElement.getAttribute("Id");
                if (locProfileId == null || locProfileId.isBlank()) {
                    throw new AIxCredentialException("XML credential Profile element is missing required Id attribute.");
                }
                EnumMap<AInCredentialType, Map<AInCredentialField, AIcCredentialValueReference>> locTypes =
                    new EnumMap<>(AInCredentialType.class);
                for (Element locTypeElement : childElements(locProfileElement)) {
                    AInCredentialType locType = credentialTypeFromPropertyName(locTypeElement.getTagName());
                    EnumMap<AInCredentialField, AIcCredentialValueReference> locFields =
                        new EnumMap<>(AInCredentialField.class);
                    for (Element locFieldElement : childElements(locTypeElement)) {
                        AInCredentialField locField;
                        try {
                            locField = AInCredentialField.fromId(locFieldElement.getTagName());
                        } catch (IllegalArgumentException aException) {
                            throw new AIxCredentialException(
                                "Credential profile '" + locProfileId + "' type '" + locType.getId() +
                                    "' contains unsupported field '" + locFieldElement.getTagName() + "'.",
                                aException
                            );
                        }
                        if (!locType.getSupportedFields().contains(locField)) {
                            throw new AIxCredentialException(
                                "Credential profile '" + locProfileId + "' type '" + locType.getId() +
                                    "' does not support field '" + locField.getId() + "'."
                            );
                        }
                        String locSource = requiredChildText(locFieldElement, AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__SOURCE, locProfileId, locType, locField);
                        String locValue = requiredChildText(locFieldElement, AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__VALUE, locProfileId, locType, locField);
                        if (childElements(locFieldElement).size() != 2) {
                            throw fieldError(locProfileId, locType, locField, "contains unsupported XML elements.");
                        }
                        try {
                            locFields.put(
                                locField,
                                new AIcCredentialValueReference(AInCredentialValueSource.fromId(locSource), locValue)
                            );
                        } catch (IllegalArgumentException aException) {
                            throw fieldError(locProfileId, locType, locField, aException.getMessage());
                        }
                    }
                    if (locTypes.put(locType, locFields) != null) {
                        throw new AIxCredentialException(
                            "Credential profile '" + locProfileId + "' contains duplicate type '" + locType.getPropertyName() + "'."
                        );
                    }
                }
                if (locProfiles.put(locProfileId, locTypes) != null) {
                    throw new AIxCredentialException("Duplicate credential profile id '" + locProfileId + "'.");
                }
            }
            try {
                return new AIcCredentialDocument(locProfiles);
            } catch (IllegalArgumentException aException) {
                throw new AIxCredentialException(aException.getMessage(), aException);
            }
        } catch (ParserConfigurationException | SAXException | IOException aException) {
            throw new AIxCredentialException("Credential document is not valid XML.", aException);
        }
    }

    private static String requiredChildText(
        Element aParent,
        String aChildName,
        String aProfileId,
        AInCredentialType aType,
        AInCredentialField aField
    ) {
        String locValue = null;
        for (Element locChild : childElements(aParent)) {
            if (aChildName.equals(locChild.getTagName())) {
                if (locValue != null) {
                    throw fieldError(aProfileId, aType, aField, "contains duplicate '" + aChildName + "' XML element.");
                }
                locValue = locChild.getTextContent();
            }
        }
        if (locValue == null) {
            throw fieldError(aProfileId, aType, aField, "is missing '" + aChildName + "' XML element.");
        }
        return locValue;
    }

    private static java.util.List<Element> childElements(Element aParent) {
        java.util.ArrayList<Element> locElements = new java.util.ArrayList<>();
        NodeList locChildren = aParent.getChildNodes();
        for (int locIndex = 0; locIndex < locChildren.getLength(); locIndex++) {
            Node locNode = locChildren.item(locIndex);
            if (locNode.getNodeType() == Node.ELEMENT_NODE) {
                locElements.add((Element) locNode);
            }
        }
        return locElements;
    }

    private static AInCredentialType credentialTypeFromPropertyName(String aPropertyName) {
        for (AInCredentialType locType : AInCredentialType.values()) {
            if (locType.getPropertyName().equals(aPropertyName)) {
                return locType;
            }
        }
        throw new AIxCredentialException("Unsupported credential type property '" + aPropertyName + "'.");
    }

    private static AIxCredentialException fieldError(
        String aProfileId,
        AInCredentialType aType,
        AInCredentialField aField,
        String aMessage
    ) {
        return new AIxCredentialException(
            "Credential '" + aProfileId + "/" + aType.getId() + "/" + aField.getId() + "' " + aMessage
        );
    }

    private static AInCredentialDocumentFormat detectFormat(BufferedInputStream aInput) {
        try {
            aInput.mark(DETECTION_PREFIX_SIZE);
            byte[] locPrefix = aInput.readNBytes(DETECTION_PREFIX_SIZE);
            aInput.reset();
            int locFirst = firstSignificantCodePoint(locPrefix);
            if (locFirst == '{' || locFirst == '[') {
                return AInCredentialDocumentFormat.JSON;
            }
            if (locFirst == '<') {
                return AInCredentialDocumentFormat.XML;
            }
            return AInCredentialDocumentFormat.YAML;
        } catch (IOException aException) {
            throw new AIxCredentialException("Cannot inspect credential document format.", aException);
        }
    }

    private static int firstSignificantCodePoint(byte[] aBytes) {
        if (aBytes.length == 0) {
            return -1;
        }
        int locOffset = 0;
        java.nio.charset.Charset locCharset = StandardCharsets.UTF_8;
        if (startsWith(aBytes, 0xEF, 0xBB, 0xBF)) {
            locOffset = 3;
        } else if (startsWith(aBytes, 0x00, 0x00, 0xFE, 0xFF)) {
            locOffset = 4;
            locCharset = java.nio.charset.Charset.forName("UTF-32BE");
        } else if (startsWith(aBytes, 0xFF, 0xFE, 0x00, 0x00)) {
            locOffset = 4;
            locCharset = java.nio.charset.Charset.forName("UTF-32LE");
        } else if (startsWith(aBytes, 0xFE, 0xFF)) {
            locOffset = 2;
            locCharset = StandardCharsets.UTF_16BE;
        } else if (startsWith(aBytes, 0xFF, 0xFE)) {
            locOffset = 2;
            locCharset = StandardCharsets.UTF_16LE;
        }
        String locText = new String(aBytes, locOffset, aBytes.length - locOffset, locCharset);
        for (int locIndex = 0; locIndex < locText.length();) {
            int locCodePoint = locText.codePointAt(locIndex);
            if (!Character.isWhitespace(locCodePoint)) {
                return locCodePoint;
            }
            locIndex += Character.charCount(locCodePoint);
        }
        return -1;
    }

    private static boolean startsWith(byte[] aBytes, int... aPrefix) {
        if (aBytes.length < aPrefix.length) {
            return false;
        }
        for (int locIndex = 0; locIndex < aPrefix.length; locIndex++) {
            if ((aBytes[locIndex] & 0xFF) != aPrefix[locIndex]) {
                return false;
            }
        }
        return true;
    }
}
