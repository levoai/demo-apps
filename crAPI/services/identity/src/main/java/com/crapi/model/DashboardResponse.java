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

package com.crapi.model;

import com.crapi.entity.CreditCard;
import com.crapi.entity.UserDetails;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.sql.Date;

@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class DashboardResponse {
    private long id;
    private String name;

    private String email;

    private String number;
    private String picture_url;
    private String video_url;
    private String video_name;
    private double available_credit;
    private long video_id;

    @JsonProperty("credit_card")
    private CreditCard creditCard;
    @JsonProperty("date_of_birth")
    private Date dateOfBirth;
    private String address;
    @JsonProperty("social_security_number")
    private String socialSecurityNumber;

    private String role;

    public void setUserDetails(UserDetails userDetails) {
        if (userDetails == null) {
            return;
        }
        name = userDetails.getName();
        available_credit = userDetails.getAvailable_credit();
        creditCard = userDetails.getCreditCard();
        dateOfBirth = userDetails.getDateOfBirth();
        address = userDetails.getAddress();
        socialSecurityNumber = userDetails.getSocialSecurityNumber();
        if (userDetails.getPicture() != null) {
            picture_url = userDetails.getPhotoBase64();
        }
    }
}
