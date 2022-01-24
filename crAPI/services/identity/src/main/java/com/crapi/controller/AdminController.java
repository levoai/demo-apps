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

import java.util.List;

import javax.servlet.http.HttpServletRequest;

import com.crapi.entity.User;
import com.crapi.exception.EntityNotFoundException;
import com.crapi.model.CRAPIResponse;
import com.crapi.service.ProfileService;
import com.crapi.service.UserService;

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

    /**
     * @param videoId
     * @param request
     * @return delete user video from database and return message
     * BFLA - Vulnerabilities
     */
    @DeleteMapping("/v2/admin/videos/{video_id}")
    public ResponseEntity<CRAPIResponse> deleteVideoBOLA(@PathVariable("video_id") Long videoId, HttpServletRequest request) {
        CRAPIResponse deleteProfileResponse = profileService.deleteAdminProfileVideo(videoId, request);
        if (deleteProfileResponse!=null && deleteProfileResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(deleteProfileResponse);
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(deleteProfileResponse);
    }

    /**
     * @param number Phone number of User being looked up
     * @return User details on success or error message.
     */
    @GetMapping("/v1/admin/users/find")
    public ResponseEntity<?> getUserByNumber(@RequestParam String number) {
        try {
            String user = userService.getUserByNumber(number);
            return ResponseEntity.status(HttpStatus.OK).body(user);
        }
        catch (EntityNotFoundException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new CRAPIResponse(e.getMessage()));
        }
    }

    /**
     * @return List (array) of User(s) details on success or error message.
     */
    @GetMapping("/v1/admin/users/list")
    public ResponseEntity<List<User>> getUsers() {
        final List<User> allUsers = userService.getUsers();

        if (allUsers.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(allUsers);
        } 

        return ResponseEntity.status(HttpStatus.OK).body(allUsers);
    }

}
