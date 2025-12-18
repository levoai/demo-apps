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
	"net/http"

	"crapi.proj/goservice/api/config"
	"crapi.proj/goservice/api/responses"
)

type Server config.Server

// Home API is for testing without token
// Below are swagger annotations for: https://github.com/swaggo/swag
// @Summary Health check API endpoint
// @Accept json
// @Produce text/plain
// @Success 200 {string} string "Welcome To This crAPI API"
// @Router /community/home [get]
func (server *Server) Home(w http.ResponseWriter, r *http.Request) {
	responses.JSON(w, http.StatusOK, "Welcome To This crAPI API")

}
