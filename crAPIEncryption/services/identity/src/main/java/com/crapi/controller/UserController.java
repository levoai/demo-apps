/*
 * Copyright 2020 Traceable, Inc.
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

import com.crapi.config.JwtProvider;
import com.crapi.constant.UserMessage;
import com.crapi.model.DashboardResponse;
import com.crapi.model.EncryptionResponse;
import com.crapi.model.LoginForm;
import com.crapi.model.CRAPIResponse;
import com.crapi.service.EncryptionService;
import com.crapi.service.UserService;
import com.crapi.utils.EncryptionUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.io.UnsupportedEncodingException;


/**
 * @author Traceable AI
 */
@CrossOrigin
@RestController
@RequestMapping("/identity/api/v2/user")
public class UserController {



    @Autowired
    UserService userService;

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;


    /**
     * @param request getting jwt token for user from request header
     * @return JSON with enc_data field containing encrypted user object with the details of vehicle and profile by token email.
     */
    @GetMapping("/dashboard")
    public ResponseEntity<EncryptionResponse> dashboard(HttpServletRequest request) throws IOException {
        DashboardResponse userData = userService.getUserByRequestToken(request);
       if (userData!=null) {
           EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(userData);
           return ResponseEntity.status(HttpStatus.OK).body(response);
       }else {
           CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.EMAIL_NOT_REGISTERED,404);
           EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
           return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
       }
    }
  
    /**
     * @param request contains JSON with enc_data field containing encrypted loginForm with email and updated password, and jwt token for user from request header
     * @return JSON with enc_data field containing encrypted reset user password for the user. first verify token and then reset user password
     */
    @PostMapping("/reset-password")
    public ResponseEntity<EncryptionResponse> resetPassword(HttpServletRequest request) throws UnsupportedEncodingException, IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        LoginForm loginForm = encryptionUtil.fromJsonString(decryptedBody, LoginForm.class);

        CRAPIResponse resetPasswordResponse = userService.resetPassword(loginForm, request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(resetPasswordResponse);
        
        if (resetPasswordResponse!=null && resetPasswordResponse.getStatus()==200) {
            return ResponseEntity.ok().body(response);
        }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

}
