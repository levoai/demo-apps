/*
 * Copyright 2022 Levo, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the “License”);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an “AS IS” BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.crapi.controller;

import com.crapi.model.CRAPIResponse;
import io.swagger.v3.oas.annotations.security.SecurityRequirements;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * @author Levo AI
 */

@SecurityRequirements
@CrossOrigin
@RestController
@RequestMapping("/identity/privacy")
public class PrivacyController {
    private static final Logger LOGGER = LogManager.getLogger(PrivacyController.class);

    /**
     * @return the user-agent header value
     */
    @GetMapping("/user_agent")
    public ResponseEntity<CRAPIResponse> healthCheck(@RequestHeader(value = "User-Agent") String userAgent){
        LOGGER.info("User agent is {}", userAgent);
        return ResponseEntity.status(HttpStatus.OK).body(new CRAPIResponse(userAgent,200));
    }
}
