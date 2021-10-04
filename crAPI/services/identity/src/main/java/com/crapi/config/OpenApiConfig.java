package com.crapi.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        
        final Info info = new Info().title("crAPI Identity Service APIs").version("1.0");
        
        final SecurityScheme jwtSecurity = new SecurityScheme().type(SecurityScheme.Type.HTTP)
                .name("Authorization").in(SecurityScheme.In.HEADER)
                .scheme("bearer").bearerFormat("JWT");

        final String securitySchemaName = "JWT";

        return new OpenAPI()
            .info(info)
            .components(new Components().addSecuritySchemes(securitySchemaName, jwtSecurity))
            .addSecurityItem(new SecurityRequirement().addList(securitySchemaName));
    }
}