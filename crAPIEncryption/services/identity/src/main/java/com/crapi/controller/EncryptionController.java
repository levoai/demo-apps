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

package com.crapi.controller;

import com.crapi.model.EncryptionRequest;
import com.crapi.model.EncryptionResponse;
import com.crapi.service.EncryptionService;
import com.crapi.utils.EncryptionUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.io.IOException;
import java.util.Map;

/**
 * Controller for encryption and decryption APIs
 */
@CrossOrigin
@RestController
@RequestMapping("/identity/api/encryption")
public class EncryptionController {

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;

    /**
     * API to encrypt data - accepts any JSON body and encrypts the entire JSON
     * @param request HTTP request containing JSON body to encrypt
     * @return JSON with enc_data field containing encrypted data
     */
    @PostMapping("/encrypt")
    public ResponseEntity<EncryptionResponse> encrypt(HttpServletRequest request) {
        try {
            // Read the entire request body as JSON string
            String requestBody = encryptionUtil.readRequestBody(request);
            
            // Encrypt the entire JSON body
            String encryptedData = encryptionService.encrypt(requestBody);
            
            return ResponseEntity.status(HttpStatus.OK).body(new EncryptionResponse(encryptedData));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new EncryptionResponse("Error: " + e.getMessage()));
        }
    }

    /**
     * API to decrypt data - expects JSON with enc_data field
     * @param request HTTP request containing JSON with enc_data field
     * @return decrypted plain text data (as JSON string)
     */
    @PostMapping("/decrypt")
    public ResponseEntity<EncryptionResponse> decrypt(HttpServletRequest request) {
        try {
            // Read and decrypt the enc_data field from request
            String decryptedData = encryptionUtil.readAndDecryptEncData(request);
            
            return ResponseEntity.status(HttpStatus.OK).body(new EncryptionResponse(decryptedData));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(new EncryptionResponse("Error: " + e.getMessage()));
        }
    }
}
