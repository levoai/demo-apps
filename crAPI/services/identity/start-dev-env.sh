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
export BLOCK_SHELL_INJECTION=false
export JWT_SECRET=crapi
export MAILHOG_HOST=localhost
export MAILHOG_PORT=1025
export MAILHOG_DOMAIN=example.com
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_EMAIL=user@example.com
export SMTP_PASS=xxxxxxxxxxxxxx
export SMTP_FROM=no-reply@example.com
export SMTP_AUTH=true
export SMTP_STARTTLS=true
      

mvn -f ./pom.xml dependency:go-offline -B 
mvn -f ./pom.xml clean package -DskipTests
java -jar ./target/user-microservices-1.0-SNAPSHOT.jar
