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
import com.crapi.entity.ProfileVideo;
import com.crapi.entity.UserDetails;
import com.crapi.model.CRAPIResponse;
import com.crapi.model.VideoForm;
import com.crapi.service.ProfileService;
import com.google.api.Http;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletRequest;
import java.io.BufferedReader;
import java.io.File;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * @author Traceable AI
 */

@CrossOrigin
@RestController
@RequestMapping("/identity")
public class ProfileController {

    @Autowired
    ProfileService profileService;


    /**
     * @param videoId
     * @param request
     * @return get profile video details.
     */
    @GetMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<?> getProfileVideo(@PathVariable("video_id") Long videoId, HttpServletRequest request) {
        ProfileVideo profileVideo = profileService.getProfileVideo(videoId, request);
        if (profileVideo!=null) {
            return ResponseEntity.status(HttpStatus.OK).body(profileVideo);
        } else {
            return ResponseEntity.status(HttpStatus.NO_CONTENT).body(new CRAPIResponse
                                         (UserMessage.VIDEO_NOT_FOUND));
        }
    }

    /**
     * @param file
     * @param request
     * @return its save and update user profile picture for token user and return updated user profile object
     */
    @PostMapping(value = "/api/v2/user/pictures")
    public ResponseEntity<?> updateProfilePicture(@RequestPart("file") MultipartFile file,HttpServletRequest request) {
        UserDetails profilePictureLink = profileService.uploadProfilePicture(file,request);
        if (profilePictureLink!=null){
            profilePictureLink.setUser(null);
            return ResponseEntity.status(HttpStatus.OK).body(profilePictureLink);
        }
        else
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new CRAPIResponse
                (UserMessage.INTERNAL_SERVER_ERROR));
    }

    /**
     * @param file
     * @param request
     * @returns update user profile video for token user and return updated user profile object
     * user video allowed up-to 10MB
     * */
    @PostMapping(value = "/api/v2/user/videos")
    public ResponseEntity<?> uploadProfileVideo(@RequestPart("file") MultipartFile file,HttpServletRequest request) {
        ProfileVideo profileVideoLink = profileService.uploadProfileVideo(file,request);
        if (profileVideoLink!=null) {
            return ResponseEntity.status(HttpStatus.OK).body(profileVideoLink);
        }
        else
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(new CRAPIResponse
                                                (UserMessage.INTERNAL_SERVER_ERROR));
    }

     /**
     * @param videoId
     * @param videoForm
     * @param request
     * @return updated profile video name and return update success message.
     */
    @PutMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<?> updateProfileVideo(@PathVariable("video_id") Long videoId, @RequestBody VideoForm videoForm, HttpServletRequest request) {
        ProfileVideo profileVideo = profileService.updateProfileVideo(videoForm, request);
        if (profileVideo!=null)
            return ResponseEntity.status(HttpStatus.OK).body(profileVideo);
        else
            return ResponseEntity.status(HttpStatus.NO_CONTENT).body(new CRAPIResponse
                                         (UserMessage.SORRY_DIDNT_GET_PROFILE));
    }

    /**
     * @param videoId
     * @param request
     * @return message that user can't delete user video
     * it give hint to user for BFLA - Vulnerabilities
     */
    @DeleteMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<?> deleteVideo(@PathVariable("video_id") Long videoId, HttpServletRequest request){
        CRAPIResponse deleteProfileResponse = profileService.deleteProfileVideo(videoId, request);
        if (deleteProfileResponse!=null && deleteProfileResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(deleteProfileResponse);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(deleteProfileResponse);
        }
    }


    /**
     * @param video_id
     * @return Shell Injection - convert video
     * its read the conversion param from the database and perform the operation according to conversion param
     * this api will be accessed by locally only
     */
    @GetMapping("api/v2/user/videos/convert_video")
    public ResponseEntity<?> convertVideoEndPoint(@RequestParam(required = false) Long video_id,
                                                  HttpServletRequest request) {
        CRAPIResponse convertVideoResponse = profileService.convertVideo(video_id, request);
        if (convertVideoResponse != null && convertVideoResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(convertVideoResponse);
        } else if (convertVideoResponse!=null && convertVideoResponse.getStatus()!=200){
            return ResponseEntity.status(HttpStatus.valueOf(convertVideoResponse.getStatus())).body(convertVideoResponse);
        }
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(convertVideoResponse);
    }

    /**
     * @param number the number of videos to list
     * @return list sample videos from library
     */
    @GetMapping("/api/v2/user/videos/list_sample_videos")
    public ResponseEntity<String> listSampleVideos(@RequestParam(required = false) String number, HttpServletRequest request) {
        try {
            InputStream in = getClass().getClassLoader().getResourceAsStream("videos.txt");
            if (in == null) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(UserMessage.INTERNAL_SERVER_ERROR);
            }
            BufferedReader reader = new BufferedReader(new InputStreamReader(in));
            String sampleVideos = reader.lines().collect(Collectors.joining("\\\\n"));
            if (number == null) {
                number = "-0";
            }
            String[] cmd = {
                    "/bin/sh",
                    "-c",
                    "printf " + sampleVideos + " | head -n " + number
            };
            Process process = Runtime.getRuntime().exec(cmd);
            String output = new BufferedReader(new InputStreamReader(process.getInputStream())).lines().collect(Collectors.joining("\n"));
            if (process.waitFor(5, TimeUnit.SECONDS)) {
                return ResponseEntity.status(HttpStatus.OK).body(output);
            } else {
                return ResponseEntity.status(HttpStatus.REQUEST_TIMEOUT).body("Request Timeout");
            }
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(UserMessage.INTERNAL_SERVER_ERROR);
        }
    }


}
