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

import com.crapi.model.EncryptionResponse;
import com.crapi.service.EncryptionService;
import com.crapi.utils.EncryptionUtil;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.Collections;
import java.util.Map;

/**
 * Simple echo controller that returns whatever JSON payload is provided.
 */

@SecurityRequirement(name = "JWT")
@PreAuthorize("hasRole('USER') or hasRole('ADMIN')")
@RestController
@CrossOrigin
@RequestMapping("/identity/api")
public class EchoController {

  @Autowired
  EncryptionService encryptionService;

  @Autowired
  EncryptionUtil encryptionUtil;

  @PostMapping(
      path = "/mirror",
      consumes = "application/json",
      produces = "application/json")
  public ResponseEntity<EncryptionResponse> echo(HttpServletRequest request) throws IOException {
    String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
    Map<String, Object> body = encryptionUtil.fromJsonString(decryptedBody, Map.class);
    
    EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(body != null ? body : Collections.emptyMap());
    
    return ResponseEntity.ok(response);
  }
}

