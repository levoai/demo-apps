package com.crapi.entity;

import com.crapi.utils.CreditCardNumberGenerator;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import org.apache.commons.lang3.RandomStringUtils;

import javax.persistence.*;
import java.util.Random;

@Entity
@Table(name = "credit_card")
@Data
public class CreditCard {

    @Id
    @JsonIgnore
    @GeneratedValue(strategy = GenerationType.AUTO)
    private long id;

    @JsonProperty("card_number")
    private String cardNumber;

    @JsonProperty("expiry_date")
    private String expiryDate;

    private int cvv;
    
    @JsonIgnore
    @OneToOne
    private User user;

    public CreditCard() {

    }

    public CreditCard(String cardNumber, String expiryDate, int cvv, User user){
        this.cardNumber = cardNumber;
        this.expiryDate = expiryDate;
        this.cvv = cvv;
        this.user = user;
    }

    public static CreditCard random(User user) {
        Random random = new Random();
        String cardNumber = CreditCardNumberGenerator.generate(random);
        String expiryDate = String.format("%02d/%02d", random.nextInt(12), random.nextInt(10) + 25);
        int cvv = new Random().nextInt(900) + 100;
        return new CreditCard(cardNumber, expiryDate, cvv, user);
    }
}
