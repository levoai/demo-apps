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


import com.crapi.constant.UserMessage;
import com.crapi.model.*;
import com.crapi.service.EncryptionService;
import com.crapi.service.OtpService;
import com.crapi.service.UserService;
import com.crapi.utils.EncryptionUtil;
import com.crapi.model.EncryptionResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.security.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.util.Map;


/**
 * @author Traceable AI
 */
@SecurityRequirements
@CrossOrigin
@RestController
@RequestMapping("/identity/api/auth")
public class AuthController {

    @Autowired
    UserService userService;

    @Autowired
    OtpService otpService;

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;


    /**
     * @param request contains JSON with enc_data field containing encrypted loginForm with user email and password for login
     * @return JSON with enc_data field containing encrypted jwt token of user
     * @throws UnsupportedEncodingException throws UnsupportedEncodingException for password encryption
     */
    @PostMapping("/login")
    public ResponseEntity<EncryptionResponse> authenticateUser(HttpServletRequest request) throws UnsupportedEncodingException, IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        LoginForm loginForm = encryptionUtil.fromJsonString(decryptedBody, LoginForm.class);
        
        JwtResponse respJwt = userService.authenticateUserLogin(loginForm);
        
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(respJwt);
        
        if ( (respJwt != null) && (respJwt.getToken() != null) ) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
        }
    }


    /**
     * @param request contains JSON with enc_data field containing encrypted signUpRequest with user email,number,name and password
     * @return JSON with enc_data field containing encrypted success and failure message after user registration.
     */
    @PostMapping("/signup")
    public ResponseEntity<EncryptionResponse> registerUser(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        SignUpForm signUpRequest = encryptionUtil.fromJsonString(decryptedBody, SignUpForm.class);
        
        // Creating user's account
        CRAPIResponse registerUserResponse = userService.registerUser(signUpRequest);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(registerUserResponse);
        
        if (registerUserResponse!=null && registerUserResponse.getStatus()==200){
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else if (registerUserResponse!=null && registerUserResponse.getStatus()==403){
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        }
        else {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }


    /**
     * @param request contains JSON with enc_data field containing encrypted forgetPassword with user email for which user want to generate otp
     * @return JSON with enc_data field containing encrypted success and failure message after generating otp
     * and sent the otp to the register email.
     */
    @PostMapping("/forget-password")
    public ResponseEntity<EncryptionResponse> forgetPassword(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        ForgetPassword forgetPassword = encryptionUtil.fromJsonString(decryptedBody, ForgetPassword.class);
        
        CRAPIResponse forgetPasswordResponse =otpService.generateOtp(forgetPassword);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(forgetPasswordResponse);
        
        if (forgetPasswordResponse!=null && forgetPasswordResponse.getStatus()==200){
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
    }

    /**
     * @param request contains JSON with enc_data field containing encrypted otpForm with otp, updated password and user email
     * @return JSON with enc_data field containing encrypted success and failure response
     * its non secure API for attacker. in this attacker can enter 'n' number of times invalid otp
     */
    @PostMapping("/v2/check-otp")
    public ResponseEntity<EncryptionResponse> checkOtp(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        OtpForm otpForm = encryptionUtil.fromJsonString(decryptedBody, OtpForm.class);
        
        CRAPIResponse validateOtpResponse = otpService.validateOtp(otpForm);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(validateOtpResponse);
        
        if (validateOtpResponse!=null && validateOtpResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }

    }

    /**
     * @param request contains JSON with enc_data field containing encrypted otpForm with otp, updated password and user email
     * @return JSON with enc_data field containing encrypted success and failure response
     * its secure otp validator in this user can enter 10 times invalid otp
     * after 10 invalid otp it will invalidate the otp.
     */
    @PostMapping("/v3/check-otp")
    public ResponseEntity<EncryptionResponse> secureCheckOtp(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        OtpForm otpForm = encryptionUtil.fromJsonString(decryptedBody, OtpForm.class);
        
        CRAPIResponse validateOtpResponse = otpService.secureValidateOtp(otpForm);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(validateOtpResponse);
        
        if (validateOtpResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }else if(validateOtpResponse.getStatus()==503) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
        }
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

    /**
     * @param request contains JSON with enc_data field containing encrypted loginWithEmailToken with user email and email change token
     * @return JSON with enc_data field containing encrypted double verification message
     */
    @PostMapping("/v4.0/user/login-with-token")
    public ResponseEntity<EncryptionResponse> loginWithToken(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        LoginWithEmailToken loginWithEmailToken = encryptionUtil.fromJsonString(decryptedBody, LoginWithEmailToken.class);
        
        CRAPIResponse apiResponse=userService.loginWithEmailToken(loginWithEmailToken);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(apiResponse);
        
        return ResponseEntity.status(HttpStatus.valueOf(apiResponse.getStatus())).body(response);
    }

    /**
     * @param request contains JSON with enc_data field containing encrypted loginWithEmailToken with user email and email change token
     * @return JSON with enc_data field containing encrypted jwt token for login with token
     */
    @PostMapping("/v2.7/user/login-with-token")
    public ResponseEntity<EncryptionResponse> loginWithTokenV2(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        LoginWithEmailToken loginWithEmailToken = encryptionUtil.fromJsonString(decryptedBody, LoginWithEmailToken.class);
        
        JwtResponse jwt = userService.loginWithEmailTokenV2(loginWithEmailToken);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(jwt);
        
        if (jwt.getToken()!=null && jwt.getToken().length()>5){
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

    

}
