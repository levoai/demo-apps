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

package controllers

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"

	"github.com/joncalhoun/qson"

	"crapi.proj/goservice/api/models"
	"crapi.proj/goservice/api/responses"
	"go.mongodb.org/mongo-driver/bson"
)

//AddNewCoupon Coupon add coupon in database
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Add a new coupon to the shop database
// @Accept json
// @Produce json
// @Param coupon body models.Coupon true "Coupon"
// @Success 200 {string} string "Coupon Added in database"
// @Failure 400 {object} string
// @Failure 500 {object} string
// @Router /community/api/v2/coupon/new-coupon [post]
//
func (s *Server) AddNewCoupon(w http.ResponseWriter, r *http.Request) {
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	coupon := models.Coupon{}
	err = json.Unmarshal(body, &coupon)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	coupon.Prepare()
	savedCoupon, er := models.SaveCoupon(s.Client, coupon)
	if er != nil {
		responses.ERROR(w, http.StatusInternalServerError, er)
	}
	if savedCoupon.CouponCode != "" {
		responses.JSON(w, http.StatusOK, "Coupon Added in database")
	}

}

//ValidateCoupon Coupon check coupon in database, if coupon code is valid it returns
//@return
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Check the validity of the coupon in the shop database.
// @Accept json
// @Produce json
// @Param coupon_code body string true "Coupon Code"
// @Success 200 {object} models.Coupon
// @Failure 400 {object} string
// @Failure 422 {object} string
// @Failure 500 {object} string
// @Router /community/api/v2/coupon/validate-coupon [post]
//
func (s *Server) ValidateCoupon(w http.ResponseWriter, r *http.Request) {

	var bsonMap bson.M

	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		fmt.Println("No payload for ValidateCoupon", body, err)
		return
	}
	err = json.Unmarshal(body, &bsonMap)
	if err != nil {
		responses.ERROR(w, http.StatusUnprocessableEntity, err)
		fmt.Println("Failed to read json body", err)
		return
	}
	couponData, err := models.ValidateCode(s.Client, s.DB, bsonMap)

	if err != nil {
		fmt.Println("Error fetching Coupon", couponData, err)
		responses.JSON(w, http.StatusInternalServerError, err)
		return
	}
	responses.JSON(w, http.StatusOK, couponData)
}

//ValidateViaGetCoupon Check if coupon present in database
//@return
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Check the validity of the coupon in the shop database.
// @Description Validate coupon code specified as query param
// @Accept json
// @Produce json
// @Param coupon_code query string true "Coupon Code"
// @Success 200 {object} models.Coupon
// @Failure 400 {object} string
// @Failure 422 {object} string
// @Failure 500 {object} string
// @Router /community/api/v2/coupon/validate-coupon [get]
//
func (s *Server) ValidateCouponViaGETv2(w http.ResponseWriter, r *http.Request) {

	couponCode := r.URL.Query().Get("coupon_code")
	if couponCode == "" {
		errorBadReq := errors.New(("Invalid request. Missing query parameter coupon_code."))
		responses.ERROR(w, http.StatusBadRequest, errorBadReq)
		return
	}

	couponCode = strings.TrimLeft(couponCode, " ")
	couponCode = strings.TrimRight(couponCode, " ")
	isJsonObject := (strings.HasPrefix(couponCode, "{") && strings.HasSuffix(couponCode, "}"))

	queryStr := ""
	if isJsonObject {
		queryStr = "{ \"coupon_code\":" + couponCode + " }"
	} else {
		queryStr = "{ \"coupon_code\":\"" + couponCode + "\" }"
	}

	var bsonMap bson.M
	err := json.Unmarshal([]byte(queryStr), &bsonMap)
	if err != nil {
		responses.ERROR(w, http.StatusUnprocessableEntity, err)
		return
	}

	// Susceptible to NoSQLi via param value injection
	couponData, err := models.ValidateCode(s.Client, s.DB, bsonMap)
	if err != nil {
		fmt.Println("Error fetching Coupon", couponData, err)
		responses.JSON(w, http.StatusInternalServerError, err)
		return
	}
	responses.JSON(w, http.StatusOK, couponData)
}

//ValidateViaGetCoupon Check if coupon present in database
//@return
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Check the validity of the coupon in the shop database.
// @Description Validate coupon code specified as query param
// @Accept json
// @Produce json
// @Param coupon_code query string true "Coupon Code"
// @Success 200 {object} models.Coupon
// @Failure 400 {object} string
// @Failure 422 {object} string
// @Failure 500 {object} string
// @Router /community/api/v1/coupon/validate-coupon [get]
//
func (s *Server) ValidateCouponViaGETv1(w http.ResponseWriter, r *http.Request) {
	queryJSON, err := qson.ToJSON(r.URL.RawQuery)
	if err != nil {
		responses.ERROR(w, http.StatusUnprocessableEntity, err)
		return
	}

	var bsonMap bson.M
	err = json.Unmarshal(queryJSON, &bsonMap)
	if err != nil {
		responses.ERROR(w, http.StatusUnprocessableEntity, err)
		return
	}

	// Susceptible to NoSQLi via the full query string
	couponData, err := models.ValidateCode(s.Client, s.DB, bsonMap)
	if err != nil {
		fmt.Println("Error fetching Coupon", couponData, err)
		responses.JSON(w, http.StatusInternalServerError, err)
		return
	}
	responses.JSON(w, http.StatusOK, couponData)
}
