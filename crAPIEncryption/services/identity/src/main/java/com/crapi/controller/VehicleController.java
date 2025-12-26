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
import com.crapi.entity.VehicleDetails;
import com.crapi.model.CRAPIResponse;
import com.crapi.model.EncryptionResponse;
import com.crapi.model.VehicleForm;
import com.crapi.model.VehicleLocationResponse;
import com.crapi.service.EncryptionService;
import com.crapi.service.VehicleService;
import com.crapi.utils.EncryptionUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.CollectionUtils;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

/**
 * @author Traceable AI
 */

@CrossOrigin
@RestController
@RequestMapping("/identity/api/v2")
public class VehicleController {

    @Autowired
    VehicleService vehicleService;

    @Autowired
    EncryptionService encryptionService;

    @Autowired
    EncryptionUtil encryptionUtil;


    /**
     * @param request contains JSON with enc_data field containing encrypted vehicleDetails
     * @return JSON with enc_data field containing encrypted response of success and failure message
     * save vehicle Details for user in database
     */
    @PostMapping("/vehicle/add_vehicle")
    public ResponseEntity<EncryptionResponse> addVehicle(HttpServletRequest request) throws IOException {
        String decryptedBody = encryptionUtil.readAndDecryptEncData(request);
        VehicleForm vehicleDetails = encryptionUtil.fromJsonString(decryptedBody, VehicleForm.class);
        
        CRAPIResponse checkVehicleResponse =vehicleService.checkVehicle(vehicleDetails, request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(checkVehicleResponse);
        
        if(checkVehicleResponse!=null && checkVehicleResponse.getStatus()==200){
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);

    }

    /**
     * @param request
     * @return JSON with enc_data field containing encrypted send vehicle details to user by email address
     */
    @PostMapping("/vehicle/resend_email")
    public ResponseEntity<EncryptionResponse> getVehicleDetails(HttpServletRequest request) throws IOException {
        CRAPIResponse vehicleResponse = vehicleService.sendVehicleDetails(request);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(vehicleResponse);
        
        if (vehicleResponse!=null && vehicleResponse.getStatus()==200) {
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }

    /**
     * @param request
     * @return JSON with enc_data field containing encrypted List of vehicle of user
     * Dashboard Vehicle details fetch by this api
     */
    @GetMapping("/vehicle/vehicles")
    public ResponseEntity<EncryptionResponse> getVehicle(HttpServletRequest request) throws IOException {
        List<VehicleDetails> vehicleDetails = vehicleService.getVehicleDetails(request);
        if (vehicleDetails!=null) {
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(vehicleDetails);
            return ResponseEntity.status(HttpStatus.OK).body(response);
        }
        CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.DID_NOT_GET_VEHICLE_FOR_USER,500);
        EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }



    /**
     * @param carId
     * @return JSON with enc_data field containing encrypted VehicleDetails on given car_id.
     */
    @GetMapping("/vehicle/{carId}/location")
    public ResponseEntity<EncryptionResponse> getLocationBOLA(@PathVariable("carId")UUID carId) throws IOException {
        VehicleLocationResponse vehicleDetails = vehicleService.getVehicleLocation(carId);
        if (vehicleDetails!=null) {
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(vehicleDetails);
            return ResponseEntity.ok().body(response);
        } else {
            CRAPIResponse errorResponse = new CRAPIResponse(UserMessage.DID_NOT_GET_VEHICLE_FOR_USER);
            EncryptionResponse response = encryptionUtil.encryptAndWrapResponseObject(errorResponse);
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
        }
    }
}
