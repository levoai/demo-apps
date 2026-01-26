package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	"github.com/owasp-crapi-workshop-api/mcp-server/config"
	"github.com/owasp-crapi-workshop-api/mcp-server/models"
	"github.com/mark3labs/mcp-go/mcp"
)

func Op_workshop_mechanic_get_svc_reportsHandler(cfg *config.APIConfig) func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	return func(ctx context.Context, request mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		args, ok := request.Params.Arguments.(map[string]any)
		if !ok {
			return mcp.NewToolResultError("Invalid arguments object"), nil
		}
		url := fmt.Sprintf("%s/workshop/api/mechanic/user_reports", cfg.BaseURL)
		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("Failed to create request", err), nil
		}
		// Set authentication based on auth type
		if cfg.BearerToken != "" {
			req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.BearerToken))
		}
		
		// Add custom headers if provided
		
		// Set client identification headers
		req.Header.Set("X-Request-Source", "Codeglide-MCP-generator")
		req.Header.Set("Accept", "application/json")
		if val, ok := args["Host"]; ok {
			req.Header.Set("Host", fmt.Sprintf("%v", val))
		}
		if val, ok := args["Content-Type"]; ok {
			req.Header.Set("Content-Type", fmt.Sprintf("%v", val))
		}
		if val, ok := args["Accept"]; ok {
			req.Header.Set("Accept", fmt.Sprintf("%v", val))
		}
		if val, ok := args["Accept-Encoding"]; ok {
			req.Header.Set("Accept-Encoding", fmt.Sprintf("%v", val))
		}

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("Request failed", err), nil
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return mcp.NewToolResultErrorFromErr("Failed to read response body", err), nil
		}

		if resp.StatusCode >= 400 {
			return mcp.NewToolResultError(fmt.Sprintf("API error: %s", body)), nil
		}
		// Use properly typed response
		var result map[string]interface{}
		if err := json.Unmarshal(body, &result); err != nil {
			// Fallback to raw text if unmarshaling fails
			return mcp.NewToolResultText(string(body)), nil
		}

		prettyJSON, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			return mcp.NewToolResultErrorFromErr("Failed to format JSON", err), nil
		}

		return mcp.NewToolResultText(string(prettyJSON)), nil
	}
}

func CreateOp_workshop_mechanic_get_svc_reportsTool(cfg *config.APIConfig) models.Tool {
	tool := mcp.NewTool("get_workshop_api_mechanic_user_reports",
		mcp.WithDescription("Get all the service reports for the currently logged in user"),
		mcp.WithString("Host", mcp.Required(), mcp.Description("")),
		mcp.WithString("Content-Type", mcp.Required(), mcp.Description("")),
		mcp.WithString("Accept", mcp.Required(), mcp.Description("")),
		mcp.WithString("Accept-Encoding", mcp.Required(), mcp.Description("")),
	)

	return models.Tool{
		Definition: tool,
		Handler:    Op_workshop_mechanic_get_svc_reportsHandler(cfg),
	}
}
