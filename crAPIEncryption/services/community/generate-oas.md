# How to generate OAS v3 JSON files?

- Install `swag` using instructions here: https://github.com/swaggo/swag
- If adding or modifying new API endpoints make sure you apply appropriate swag 
annotations to the code
- From the community service root dir run `$GOPATH/swag init -d ./api/controllers -d ./`
- This will generate swagger 2.0 JSON & YAML files in the ./docs dir
- Now you will have to manually convert this to OpenAPI v3 format using Swagger Editor, and do some minor fixups (e.g fix ups for AuthN/AuthZ, etc.)