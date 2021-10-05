import React, { useCallback, useEffect } from "react";
import SwaggerUI from "swagger-ui-react"
import "swagger-ui-react/swagger-ui.css"
import { message } from "antd";

const ApiExplorer = ({ accessToken }) => {

    const specUrl="https://raw.githubusercontent.com/levoai/demo-apps/main/crAPI/api-specs/openapi.json"

    const [apiSpec, setApiSpec] = React.useState({})

    function handleResponse(specString) {
        let specObj = JSON.parse(specString)
        const baseUrl = window.location.protocol + "//"
            + window.location.hostname + ":" + window.location.port
        specObj['servers'] = [{ 'url': baseUrl }]
        setApiSpec(specObj)
    }

    useEffect(() => {

        function fetchApiSpec() {
            fetch(specUrl).then((response) => response.text())
                .then(handleResponse)
                .catch((err) => {
                    message.error("Unable to fetch the API specs for crAPI!");
                });    
        }

        fetchApiSpec()
    }, [accessToken]);

    const handleSwaggerOnLoad = useCallback((system) => {
        system.preauthorizeApiKey("bearerAuth", accessToken)
    },[accessToken])

    return (
        (Object.keys(apiSpec).length === 0) ? 
            <SwaggerUI url={""} /> : <SwaggerUI spec={apiSpec} onComplete={handleSwaggerOnLoad} />
           
    );
}

export default (ApiExplorer)