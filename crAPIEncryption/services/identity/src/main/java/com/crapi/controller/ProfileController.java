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
import com.crapi.model.EncryptionResponse;
import com.crapi.model.VideoForm;
import com.crapi.service.EncryptionService;
import com.crapi.service.ProfileService;
import com.crapi.utils.EncryptionUtil;
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
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.*;  

/**
 * @author Traceable AI
 */

@CrossOrigin
@RestController
@RequestMapping("/identity")
public class ProfileController {

    @Autowired
    ProfileService profileService;

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;


    /**
     * @param videoId
     * @param request
     * @return JSON with enc_data field containing encrypted profile video details.
     */
    @GetMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<EncryptionResponse> getProfileVideo(@PathVariable("video_id") Long videoId, HttpServletRequest request) throws IOException {
        ProfileVideo profileVideo = profileService.getProfileVideo(videoId, request);
        if (profileVideo!=null) {
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(profileVideo);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        } else {
            CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.VIDEO_NOT_FOUND);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.NO_CONTENT).body(response);
        }
    }

    /**
     * @param file
     * @param request
     * @return JSON with enc_data field containing encrypted its save and update user profile picture for token user and return updated user profile object
     */
    @PostMapping(value = "/api/v2/user/pictures")
    public ResponseEntity<EncryptionResponse> updateProfilePicture(@RequestPart("file") MultipartFile file,HttpServletRequest request) throws IOException {
        UserDetails profilePictureLink = profileService.uploadProfilePicture(file,request);
        if (profilePictureLink!=null){
            profilePictureLink.setUser(null);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(profilePictureLink);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else {
            CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.INTERNAL_SERVER_ERROR);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

    /**
     * @param file
     * @param request
     * @returns JSON with enc_data field containing encrypted update user profile video for token user and return updated user profile object
     * user video allowed up-to 10MB
     * */
    @PostMapping(value = "/api/v2/user/videos")
    public ResponseEntity<EncryptionResponse> uploadProfileVideo(@RequestPart("file") MultipartFile file,HttpServletRequest request) throws IOException {
        ProfileVideo profileVideoLink = profileService.uploadProfileVideo(file,request);
        if (profileVideoLink!=null) {
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(profileVideoLink);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else {
            CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.INTERNAL_SERVER_ERROR);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }

     /**
     * @param videoId
     * @param request contains JSON with enc_data field containing encrypted videoForm
     * @return JSON with enc_data field containing encrypted updated profile video name and return update success message.
     */
    @PutMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<EncryptionResponse> updateProfileVideo(@PathVariable("video_id") Long videoId, HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        VideoForm videoForm = encryptionUtil.fromJsonString(decryptedBody, VideoForm.class);
        
        ProfileVideo profileVideo = profileService.updateProfileVideo(videoForm, request);
        if (profileVideo!=null) {
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(profileVideo);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        else {
            CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.SORRY_DIDNT_GET_PROFILE);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.NO_CONTENT).body(response);
        }
    }

    /**
     * @param videoId
     * @param request
     * @return JSON with enc_data field containing encrypted message that user can't delete user video
     * it give hint to user for BFLA - Vulnerabilities
     */
    @DeleteMapping("/api/v2/user/videos/{video_id}")
    public ResponseEntity<EncryptionResponse> deleteVideo(@PathVariable("video_id") Long videoId, HttpServletRequest request) throws IOException {
        CRAPIResponse deleteProfileResponse = profileService.deleteProfileVideo(videoId, request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(deleteProfileResponse);
        if (deleteProfileResponse!=null && deleteProfileResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        }
    }


    /**
     * @param video_id
     * @return JSON with enc_data field containing encrypted Shell Injection - convert video response
     * its read the conversion param from the database and perform the operation according to conversion param
     * this api will be accessed by locally only
     */
    @GetMapping("api/v2/user/videos/convert_video")
    public ResponseEntity<EncryptionResponse> convertVideoEndPoint(@RequestParam(required = false) Long video_id,
                                                  HttpServletRequest request) throws IOException {
        CRAPIResponse convertVideoResponse = profileService.convertVideo(video_id, request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(convertVideoResponse);
        if (convertVideoResponse != null && convertVideoResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        } else if (convertVideoResponse!=null && convertVideoResponse.getStatus()!=200){
            return ResponseEntity.status(HttpStatus.valueOf(convertVideoResponse.getStatus())).body(response);
        }
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
    }

    /**
     * 
     * @param number
     * @return true if the `number` string has potential command injections that should be prevented.
     * Other false.
     */
    private boolean IsCMDiRestricted(final String number) {

        if (number == null || number == "") {
            return false;
        }

        // Has the `number` parameter been injected?
        try {
            Integer.parseInt(number);
            return false; // Not injected as it parsed successfully as a number
        }
        catch (NumberFormatException ex){
            // This is an injected number that potentially has a CMDi
        }

        // Restrict the command injection to just `cat /etc/passwd`, when RESTRICT_CMDI
        // environment variable is set to true. This is to prevent hackers fully exploiting
        // hosted crAPI instances in Levo's GKE.
        final String CMDi = System.getenv("RESTRICT_CMDI");
        final boolean restrictCMDi  = Boolean.parseBoolean(CMDi); 

        if (!restrictCMDi) {
            return false;
        }
        
        // Below are the two injection characters for command exec
        final int semiColOP = number.indexOf(";");
        final int pipeOP = number.indexOf("|");
        final int andOP = number.indexOf("&");
        
        if ( (semiColOP == -1) && (pipeOP == -1) && (andOP == -1)) {
            return false;
        }

        // We have potentially atleast one or more injection operators. Lets find
        // the index of the first injection operator
        List<Integer> opIndices = new ArrayList<Integer>();  
        if (semiColOP != -1) {
            opIndices.add(semiColOP);
        }
        if (pipeOP != -1) {
            opIndices.add(pipeOP);
        }
        if (andOP != -1) {
            opIndices.add(andOP);
        }
        Collections.sort(opIndices);
        final int firstOPIndex = opIndices.get(0);

        // We only want to allow 'cat /etc/passwd' as an injection string
        final int injCmd = number.indexOf("cat /etc/passwd");
        if ( (injCmd == -1) || ( (injCmd - firstOPIndex) != 1) ) {
            return true;
        }

        return false;
    }

    /**
     * @param number the number of videos to list
     * @return JSON with enc_data field containing encrypted list sample videos from library
     */
    @GetMapping("/api/v2/user/videos/list_sample_videos")
    public ResponseEntity<EncryptionResponse> listSampleVideos(@RequestParam(required = false) String number, HttpServletRequest request) throws IOException {
        try {
            InputStream in = getClass().getClassLoader().getResourceAsStream("videos.txt");
            if (in == null) {
                EncryptionResponse errorResponse = encryptionUtil.encryptAndWrapResponseObject(UserMessage.INTERNAL_SERVER_ERROR);
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
            }
            BufferedReader reader = new BufferedReader(new InputStreamReader(in));
            String sampleVideos = reader.lines().collect(Collectors.joining("\\\\n"));
            
            if (number == null) {
                number = "-0";
            } else if (IsCMDiRestricted(number)) {
                EncryptionResponse errorResponse = encryptionUtil.encryptAndWrapResponseObject(UserMessage.ERROR);
                return ResponseEntity.status(HttpStatus.UNAVAILABLE_FOR_LEGAL_REASONS).body(errorResponse);
            }
            
            String[] cmd = {
                    "/bin/sh",
                    "-c",
                    "printf " + sampleVideos + " | head -n " + number
            };
            Process process = Runtime.getRuntime().exec(cmd);
            String output = new BufferedReader(new InputStreamReader(process.getInputStream())).lines().collect(Collectors.joining("\n"));
            if (process.waitFor(5, TimeUnit.SECONDS)) {
                EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(output);
                return ResponseEntity.status(HttpStatus.OK).body(response);
            } else {
                EncryptionResponse timeoutResponse = encryptionUtil.encryptAndWrapResponseObject("Request Timeout");
                return ResponseEntity.status(HttpStatus.REQUEST_TIMEOUT).body(timeoutResponse);
            }
        } catch (Exception e) {
            EncryptionResponse errorResponse = encryptionUtil.encryptAndWrapResponseObject(UserMessage.INTERNAL_SERVER_ERROR);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }


}
