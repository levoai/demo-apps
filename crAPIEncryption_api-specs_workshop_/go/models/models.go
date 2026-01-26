package models

import (
	"context"
	"github.com/mark3labs/mcp-go/mcp"
)

type Tool struct {
	Definition mcp.Tool
	Handler    func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error)
}

// Order represents the Order schema from the OpenAPI specification
type Order struct {
	Status string `json:"status,omitempty"`
	User User `json:"user"`
	Created_on string `json:"created_on"`
	Id int `json:"id"`
	Product Product `json:"product"`
	Quantity int `json:"quantity,omitempty"`
}

// User represents the User schema from the OpenAPI specification
type User struct {
	Email string `json:"email"`
	Number string `json:"number,omitempty"`
}

// NewProduct represents the NewProduct schema from the OpenAPI specification
type NewProduct struct {
	Image_url string `json:"image_url"`
	Name string `json:"name"`
	Price string `json:"price"`
}

// Product represents the Product schema from the OpenAPI specification
type Product struct {
	Image_url string `json:"image_url"`
	Name string `json:"name"`
	Price string `json:"price"`
	Id int `json:"id"`
}

// ProductQuantity represents the ProductQuantity schema from the OpenAPI specification
type ProductQuantity struct {
	Quantity int `json:"quantity"`
	Product_id int `json:"product_id"`
}

// ServiceRequests represents the ServiceRequests schema from the OpenAPI specification
type ServiceRequests struct {
	Service_requests []map[string]interface{} `json:"service_requests"`
}
