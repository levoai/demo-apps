package com.crapi.repository;

import com.crapi.entity.CreditCard;
import com.crapi.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CreditCardRepository extends JpaRepository<CreditCard,Long> {

    CreditCard findByUser(User user);
}
