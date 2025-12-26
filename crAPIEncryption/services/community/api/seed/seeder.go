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

package seed

import (
	"context"
	"fmt"
	"os"
	"time"

	"crapi.proj/goservice/api/models"
	"github.com/jinzhu/gorm"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

//initialize coupons data
var coupons = []models.Coupon{
	models.Coupon{
		CouponCode: "TRAC075",
		Amount:     "75",
		CreatedAt:  time.Now(),
	},
	models.Coupon{
		CouponCode: "TRAC065",
		Amount:     "65",
		CreatedAt:  time.Now(),
	},
	models.Coupon{
		CouponCode: "TRAC125",
		Amount:     "125",
		CreatedAt:  time.Now(),
	},
}

//initialize Post data
var posts = []models.Post{
	models.Post{
		Title:   "I love the crAPI forum!",
		Content: "The CrAPI forum allows me to socialize with like minded auto enthusiasts.",
	},
	models.Post{
		Title:   "The discussions are awesome!",
		Content: "I learn a lot about cars from these discussions!",
	},
	models.Post{
		Title:   "The forum makes crAPI more engaging.",
		Content: "Lively discussions with fellow enthusiasts make the forum a joy to hang out!",
	},
}
var emails = [3]string{"victim.one@example.com", "victim.two@example.com", "hacker@darkweb.com"}

//
func LoadMongoData(mongoClient *mongo.Client, db *gorm.DB) {
	var couponResult interface{}
	var postResult interface{}
	collection := mongoClient.Database(os.Getenv("MONGO_DB_NAME")).Collection("coupons")
	// get a MongoDB document using the FindOne() method
	err := collection.FindOne(context.TODO(), bson.D{}).Decode(&couponResult)
	if err != nil {
		for i, _ := range coupons {
			couponData, err := collection.InsertOne(context.TODO(), coupons[i])
			fmt.Println(couponData, err)
		}
	}
	postCollection := mongoClient.Database(os.Getenv("MONGO_DB_NAME")).Collection("post")
	er := postCollection.FindOne(context.TODO(), bson.D{}).Decode(&postResult)
	if er != nil {
		for j, _ := range posts {
			models.FindAuthorByEmail(emails[j], db)
			posts[j].Prepare()
			models.SavePost(mongoClient, posts[j])
			//postData, err := collection.InsertOne(context.TODO(), posts[j])
			//fmt.Println(postData, err)
		}
	}
}
