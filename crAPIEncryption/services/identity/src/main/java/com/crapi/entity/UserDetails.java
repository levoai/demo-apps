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

package com.crapi.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.github.javafaker.Faker;
import lombok.Data;

import javax.persistence.*;
import java.sql.Date;
import java.util.Base64;

/**
 * @author Traceable AI
 */

@Entity
@Table(name = "user_details")
@Data
public class UserDetails {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "user_details_generator")
    @SequenceGenerator(name = "user_details_generator", sequenceName = "user_details_id_seq", allocationSize = 1)
    private long id;
    private String name = "";
    private String status;
    private double available_credit;
    @Lob
    private byte[] picture;

    @OneToOne
    private User user;

    @OneToOne
    private CreditCard creditCard;
    private Date dateOfBirth;
    private String address;
    private String socialSecurityNumber;

    public void generatePiiValues() {
        creditCard = CreditCard.random(user);
        Faker faker = new Faker();
        dateOfBirth = new Date(faker.date().birthday().getTime());
        address = faker.address().fullAddress();
        socialSecurityNumber = faker.idNumber().ssnValid();
    }

    @JsonIgnore
    public byte[] getPicture() {
        return picture;
    }

    @JsonProperty("picture")
    public String getPhotoBase64() {
        // just assuming it is a jpeg. you would need to cater for different media types
        return "data:image/jpeg;base64," + new String(Base64.getEncoder().encode(picture));
    }
}
