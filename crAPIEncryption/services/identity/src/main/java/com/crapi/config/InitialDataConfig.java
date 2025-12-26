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

package com.crapi.config;


import com.crapi.entity.User;
import com.crapi.entity.UserDetails;
import com.crapi.entity.VehicleDetails;
import com.crapi.enums.ERole;
import com.crapi.enums.EStatus;
import com.crapi.repository.CreditCardRepository;
import com.crapi.repository.ProfileVideoRepository;
import com.crapi.repository.UserDetailsRepository;
import com.crapi.repository.UserRepository;
import com.crapi.repository.VehicleDetailsRepository;
import com.crapi.repository.VehicleLocationRepository;
import com.crapi.repository.VehicleModelRepository;
import com.crapi.service.VehicleService;
import com.crapi.utils.VehicleLocationData;
import com.crapi.utils.VehicleModelData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;

/**
 * @author Traceable AI
 */
@Component
public class InitialDataConfig {

    private static final Logger logger = LoggerFactory.getLogger(InitialDataConfig.class);

    @Autowired
    VehicleLocationRepository vehicleLocationRepository;

    @Autowired
    VehicleModelRepository vehicleModelRepository;

    @Autowired
    VehicleDetailsRepository vehicleDetailsRepository;

    @Autowired
    UserDetailsRepository userDetailsRepository;

    @Autowired
    CreditCardRepository creditCardRepository;

    @Autowired
    UserRepository userRepository;

    @Autowired
    ProfileVideoRepository profileVideoRepository;

    @Autowired
    VehicleService vehicleService;

    @Autowired
    PasswordEncoder encoder;


    public void addLocation() {
        if (CollectionUtils.isEmpty(vehicleLocationRepository.findAll())) {
            VehicleLocationData vehicleLocationData = new VehicleLocationData();
            vehicleLocationRepository.saveAll(vehicleLocationData.getVehicleLocationData());
        }
    }

    public void addVehicleModel() {
        if (CollectionUtils.isEmpty(vehicleModelRepository.findAll())) {
            VehicleModelData vehicleModelData = new VehicleModelData();
            vehicleModelRepository.saveAll(vehicleModelData.getModelList());
        }
    }

    @EventListener
    public void setup(ApplicationReadyEvent event) {

        addLocation();
        addVehicleModel();
        addUser();
    }

    public void addUser() {
        if (CollectionUtils.isEmpty(userDetailsRepository.findAll())) {
            addInitialUsers();
            // Mechanics are created in the workshop service
            addInitialAdmins();
        }
    }

    private void addInitialUsers() {
        boolean user1 = predefineUserData("Victim One", "victim.one@example.com",
                ERole.ROLE_USER, "4156895423", "Victim1One",
                "649acfac-10ea-43b3-907f-752e86eff2b6", "0BZCX25UTBJ987271");

        boolean user2 = predefineUserData("Victim Two", "victim.two@example.com",
                ERole.ROLE_USER, "9876570006", "Victim2Two",
                "8b9edbde-d74d-4773-8c9f-adb65c6056fc", "4NGPB83BRXL720409");

        boolean user3 = predefineUserData("Hacker", "hacker@darkweb.com",
                ERole.ROLE_USER, "7000070007", "Hack3r$$$",
                "abac4018-5a38-466c-ab7f-361908afeab6", "5JTGZ48TPYP220157");

        if (!user1 || !user2 || !user3) {
            logger.error("Failed to add predefined users.");
        }
    }

    private void addInitialAdmins() {
        boolean user1 = predefineUserData("Admin One", "admin.one@example.com",
                ERole.ROLE_ADMIN, "6052895429", "Admin1One",
                "edee0263-0179-4d9e-9ab5-90e4e64afb34", "5NPDH4AE0DH213924");

        boolean user2 = predefineUserData("Admin Two", "admin.two@example.com",
                ERole.ROLE_ADMIN, "4258221234", "Admin2Two",
                "836fe80c-02f9-4fc0-8fbd-fcdf637bb9c2", "JH4KA96633C000632");

        if (!user1 || !user2) {
            logger.error("Failed to add predefined administrators.");
        }
    }

    private boolean predefineUserData(String name, String email, ERole role, String number,
                                      String password, String vehicleUuidHexDigitString, String VIN) {
        try {
            User loginForm = new User(email, number, encoder.encode(password), role);
            loginForm = userRepository.save(loginForm);
            UserDetails userDetails = new UserDetails();
            userDetails.setName(name);
            userDetails.setUser(loginForm);
            userDetails.setAvailable_credit(100.0);
            userDetails.setStatus(EStatus.ACTIVE.toString());
            userDetails.generatePiiValues();
            creditCardRepository.save(userDetails.getCreditCard());
            userDetailsRepository.save(userDetails);
            VehicleDetails vehicleDetails = vehicleService.createVehicle(vehicleUuidHexDigitString, VIN);
            if (vehicleDetails != null) {
                vehicleDetails.setOwner(loginForm);
                vehicleDetailsRepository.save(vehicleDetails);
                return true;
            }
            logger.error("Failed to create vehicle for user {}", email);
            return false;
        } catch (Exception e) {
            logger.error("Fail to create user {}, Exception :: {}", email, e);
            return false;
        }
    }

}
