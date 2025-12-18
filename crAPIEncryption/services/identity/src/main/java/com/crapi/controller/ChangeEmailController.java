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

import com.crapi.model.ChangeEmailForm;
import com.crapi.model.CRAPIResponse;
import com.crapi.model.EncryptionResponse;
import com.crapi.service.EncryptionService;
import com.crapi.service.UserService;
import com.crapi.utils.EncryptionUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.io.IOException;

@CrossOrigin
@RestController
@RequestMapping("/identity/api")
public class ChangeEmailController {

    @Autowired
    UserService userService;

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;

    /**
     * @param request contains JSON with enc_data field containing encrypted changeEmailForm with old email and new email, api will send change email token to new email address, and jwt token for user from request header
     * @return JSON with enc_data field containing encrypted first check email is already registered or not if it is there then
     * return email already registered then try with new email.
     */
    @PostMapping("/v2/user/change-email")
    public ResponseEntity<EncryptionResponse> changesEmail(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        ChangeEmailForm changeEmailForm = encryptionUtil.fromJsonString(decryptedBody, ChangeEmailForm.class);
        
        CRAPIResponse changeEmailResponse = userService.changeEmailRequest(request,changeEmailForm);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(changeEmailResponse);
        
        if (changeEmailResponse!=null && changeEmailResponse.getStatus()==403) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        }else if (changeEmailResponse!=null && changeEmailResponse.getStatus()==404) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        }
            return ResponseEntity.status(HttpStatus.OK).body(response);

    }

    /**
     * @param request contains JSON with enc_data field containing encrypted changeEmailForm with old email and new email, with token, this function will verify email and token, and jwt token for user from request header
     * @return JSON with enc_data field containing encrypted verify token if it is valid then it will update the user email
     */
    @PostMapping("/v2/user/verify-email-token")
    public ResponseEntity<EncryptionResponse> verifyEmailToken(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        ChangeEmailForm changeEmailForm = encryptionUtil.fromJsonString(decryptedBody, ChangeEmailForm.class);
        
        CRAPIResponse verifyEmailTokenResponse = userService.verifyEmailToken(request,changeEmailForm);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(verifyEmailTokenResponse);
        
        if (verifyEmailTokenResponse!=null && verifyEmailTokenResponse.getStatus()==200){
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else if(verifyEmailTokenResponse!=null && verifyEmailTokenResponse.getStatus()==404){
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        }

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

}
