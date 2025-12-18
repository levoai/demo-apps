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

import java.io.IOException;
import java.util.List;

import javax.servlet.http.HttpServletRequest;

import com.crapi.entity.User;
import com.crapi.exception.EntityNotFoundException;
import com.crapi.model.CRAPIResponse;
import com.crapi.model.EncryptionResponse;
import com.crapi.service.ProfileService;
import com.crapi.service.UserService;
import com.crapi.utils.EncryptionUtil;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * @author Traceable AI
 */

@CrossOrigin
@RestController
@RequestMapping("/identity/api")
public class AdminController {

    @Autowired
    ProfileService profileService;

    @Autowired
    UserService userService;

    @Autowired
    EncryptionUtil encryptionUtil;

    /**
     * @param videoId
     * @param request
     * @return JSON with enc_data field containing encrypted delete user video from database and return message
     * BFLA - Vulnerabilities
     */
    @DeleteMapping("/v2/admin/videos/{video_id}")
    public ResponseEntity<EncryptionResponse> deleteVideoBOLA(@PathVariable("video_id") Long videoId, HttpServletRequest request) throws IOException {
        CRAPIResponse deleteProfileResponse = profileService.deleteAdminProfileVideo(videoId, request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(deleteProfileResponse);
        if (deleteProfileResponse!=null && deleteProfileResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
    }

    /**
     * @param number Phone number of User being looked up
     * @return JSON with enc_data field containing encrypted User details on success or error message.
     */
    @GetMapping("/v1/admin/users/find")
    public ResponseEntity<EncryptionResponse> getUserByNumber(@RequestParam String number) throws IOException {
        try {
            String user = userService.getUserByNumber(number);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(user);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        catch (EntityNotFoundException e) {
            CRAPIResponse errorResponse = new CRAPIResponse(e.getMessage());
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        }
    }

    /**
     * @return JSON with enc_data field containing encrypted List (array) of User(s) details on success or error message.
     */
    @GetMapping("/v1/admin/users/list")
    public ResponseEntity<EncryptionResponse> getUsers() throws IOException {
        final List<User> allUsers = userService.getUsers();

        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(allUsers);
        if (allUsers.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        } 

        return ResponseEntity.status(HttpStatus.OK).body(response);
    }

}
