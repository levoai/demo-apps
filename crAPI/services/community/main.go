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

package main

import (
	"crapi.proj/goservice/api"
)

// Below are swagger annotations for: https://github.com/swaggo/swag
// @title crAPI Commmunity Service API
// @version 1.0
// @description Community & forum API endpoints for crAPI.
// @contact.name Levo Support
// @contact.email support@levo.ai
// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html
// @query.collection.format multi
func main() {
	api.Run()
}
