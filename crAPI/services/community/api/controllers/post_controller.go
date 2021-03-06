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
	"io/ioutil"
	"net/http"

	"crapi.proj/goservice/api/models"
	"crapi.proj/goservice/api/responses"
	"github.com/gorilla/mux"
)

//AddNewPost add post in database,
//@return HTTP Status
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Add a new post to the user forum.
// @Accept json
// @Produce json
// @Param new_post body models.Post true "New Post"
// @Success 200 {object} models.Post
// @Failure 400 {object} string
// @Failure 500 {object} string
// @Router /community/api/v2/community/posts [post]
//
func (s *Server) AddNewPost(w http.ResponseWriter, r *http.Request) {

	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	post := models.Post{}

	err = json.Unmarshal(body, &post)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	post.Prepare()

	savedPost, err := models.SavePost(s.Client, post)
	if err != nil {
		responses.ERROR(w, http.StatusInternalServerError, err)
	}

	responses.JSON(w, http.StatusOK, savedPost)
}

//GetPostByID fetch the post by ID,
//@return HTTP Status
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Fetch the post identified by the "postID".
// @Accept json
// @Produce json
// @Param postID path int true "postID"
// @Success 200 {object} models.Post
// @Failure 400 {object} string
// @Router /community/api/v2/community/posts/{postID} [get]
//
func (s *Server) GetPostByID(w http.ResponseWriter, r *http.Request) {

	vars := mux.Vars(r)
	//var autherID uint64
	GetPost, er := models.GetPostByID(s.Client, vars["postID"])
	if er != nil {
		responses.ERROR(w, http.StatusBadRequest, er)
	}

	responses.JSON(w, http.StatusOK, GetPost)

}

//GetPost Vulnerabilities
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Get the most recent posts in the forum.
// @Accept json
// @Produce json
// @Success 200 {array} models.Post
// @Failure 500 {object} string
// @Router /community/api/v2/community/posts/recent [get]
//
func (s *Server) GetPost(w http.ResponseWriter, r *http.Request) {
	//post := models.Post{}

	posts, err := models.FindAllPost(s.Client)
	if err != nil {
		responses.ERROR(w, http.StatusInternalServerError, err)
		return
	}
	responses.JSON(w, http.StatusOK, posts)
}

//Comment will add comment in perticular post,
//@return HTTP Post Object
//@params ResponseWriter, Request
//Server have database connection
//
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Add a new comment to the post identified by the "postID".
// @Accept json
// @Produce json
// @Param postID path int true "postID"
// @Success 200 {object} models.Post
// @Failure 400 {object} string
// @Failure 500 {object} string
// @Router /community/api/v2/community/posts/{postID}/comment [post]
//
func (s *Server) Comment(w http.ResponseWriter, r *http.Request) {

	vars := mux.Vars(r)
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	comment := models.Comments{}

	err = json.Unmarshal(body, &comment)
	if err != nil {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	if vars["postID"] == "" {
		responses.ERROR(w, http.StatusBadRequest, err)
		return
	}
	comment.ID = vars["postID"]
	postData, er := models.CommentOnPost(s.Client, comment)
	if er != nil {
		responses.ERROR(w, http.StatusInternalServerError, er)
		return
	}
	responses.JSON(w, http.StatusOK, postData)
}
