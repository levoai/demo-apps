package main

import (
	"github.com/owasp-crapi-workshop-api/mcp-server/config"
	"github.com/owasp-crapi-workshop-api/mcp-server/models"
	tools_workshop_shop "github.com/owasp-crapi-workshop-api/mcp-server/tools/workshop_shop"
	tools_workshop_mechanic "github.com/owasp-crapi-workshop-api/mcp-server/tools/workshop_mechanic"
)

func GetAll(cfg *config.APIConfig) []models.Tool {
	return []models.Tool{
		tools_workshop_shop.CreateOp_workshop_shop_create_orderTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_get_tokenTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_update_orderTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_apply_couponTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_create_service_reportTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_get_mech_svc_reportsTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_signupTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_get_ordersTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_get_svc_reportsTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_contact_mechanicTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_return_purchaseTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_get_productsTool(cfg),
		tools_workshop_shop.CreateOp_workshop_shop_create_productTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_get_mechanicsTool(cfg),
		tools_workshop_mechanic.CreateOp_workshop_mechanic_get_svc_reportTool(cfg),
	}
}
