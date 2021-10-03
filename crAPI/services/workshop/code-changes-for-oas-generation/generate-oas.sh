#! /bin/sh

# Copyright 2021 Levo, Inc.
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

export DB_NAME=crapi
export DB_USER=admin
export DB_PASSWORD=crapisecretpassword
export DB_HOST=localhost
export DB_PORT=5432
export MONGO_DB_HOST=localhost
export MONGO_DB_PORT=27017
export MONGO_DB_USER=admin
export MONGO_DB_PASSWORD=crapisecretpassword
export MONGO_DB_NAME=crapi
export JWT_SECRET=crapi
export SECRET_KEY=crapi

./manage.py spectacular --file schema.yml
