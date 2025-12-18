/*
 * Copyright 2020 Traceable, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.crapi.utils;

import com.crapi.model.EncryptionResponse;
import com.crapi.service.EncryptionService;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.servlet.http.HttpServletRequest;
import java.io.BufferedReader;
import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;

/**
 * Utility class for encryption/decryption operations
 */
@Component
public class EncryptionUtil {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Autowired
    private EncryptionService encryptionService;

    /**
     * Reads the request body as a string
     */
    public String readRequestBody(HttpServletRequest request) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = request.getReader()) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
        }
        return sb.toString();
    }

    /**
     * Converts object to JSON string
     */
    public String toJsonString(Object obj) throws IOException {
        return objectMapper.writeValueAsString(obj);
    }

    /**
     * Parses JSON string to object
     */
    public <T> T fromJsonString(String json, Class<T> clazz) throws IOException {
        return objectMapper.readValue(json, clazz);
    }

    /**
     * Reads JSON or form-encoded request body and extracts encrypted data from enc_data field, then decrypts it
     * Supports both JSON format: {"enc_data": "..."} and URL-encoded format: enc_data=...
     * @param request HTTP request
     * @return decrypted string from enc_data field
     * @throws IOException if reading or parsing fails
     */
    public String readAndDecryptEncData(HttpServletRequest request) throws IOException {
        String requestBody = readRequestBody(request);
        String encryptedData = null;
        
        // Try to parse as JSON first
        try {
            JsonNode jsonNode = objectMapper.readTree(requestBody);
            if (jsonNode.has("enc_data")) {
                encryptedData = jsonNode.get("enc_data").asText();
            }
        } catch (Exception e) {
            // Not JSON, try URL-encoded form data
        }
        
        // If not found in JSON, try URL-encoded form data format
        if (encryptedData == null) {
            if (requestBody.startsWith("enc_data=")) {
                String encodedValue = requestBody.substring("enc_data=".length());
                try {
                    encryptedData = URLDecoder.decode(encodedValue, StandardCharsets.UTF_8.toString());
                } catch (Exception e) {
                    // If URL decoding fails, use the value as-is (might already be decoded)
                    encryptedData = encodedValue;
                }
            } else {
                throw new IllegalArgumentException("Request body must contain 'enc_data' field in JSON or URL-encoded format");
            }
        }
        
        if (encryptedData == null || encryptedData.isEmpty()) {
            throw new IllegalArgumentException("Request body must contain 'enc_data' field with a non-empty value");
        }
        
        return encryptionService.decrypt(encryptedData);
    }

    /**
     * Encrypts the response data and wraps it in a JSON object with enc_data field
     * @param responseData the data to encrypt (will be converted to JSON string first)
     * @return JSON string with format {"enc_data": "<encrypted_data>"}
     * @throws IOException if serialization fails
     */
    public String encryptAndWrapResponse(Object responseData) throws IOException {
        String responseJson = toJsonString(responseData);
        String encryptedResponse = encryptionService.encrypt(responseJson);
        
        ObjectNode wrapper = objectMapper.createObjectNode();
        wrapper.put("enc_data", encryptedResponse);
        return objectMapper.writeValueAsString(wrapper);
    }

    /**
     * Encrypts the response data and returns an EncryptionResponse object
     * @param responseData the data to encrypt (will be converted to JSON string first)
     * @return EncryptionResponse object with encrypted data in enc_data field
     * @throws IOException if serialization fails
     */
    public EncryptionResponse encryptAndWrapResponseObject(Object responseData) throws IOException {
        String responseJson = toJsonString(responseData);
        String encryptedResponse = encryptionService.encrypt(responseJson);
        return new EncryptionResponse(encryptedResponse);
    }
}
