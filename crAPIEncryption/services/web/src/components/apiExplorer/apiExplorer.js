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

import "./apiExplorer.css";

import React from "react";
import PropTypes from "prop-types";
import {
  Tabs
} from "antd";

import OasUI from "../oasUI/oasUI";


const { TabPane } = Tabs;

const ApiExplorer = ({history, accessToken}) => {

  const fullSpecUrl="https://raw.githubusercontent.com/levoai/demo-apps/main/crAPI/api-specs/openapi.json"
  const demoSpecUrl="https://raw.githubusercontent.com/levoai/demo-apps/main/crAPI/api-specs/demo%20scenarios/onboarding-scenarios.json"

  const renderOasUI = () => {
    return (<Tabs defaultActiveKey="1" className="apiexplorer__tabs">
      <TabPane tab="APIs Under Test" key="1" size="small">
        <OasUI accessToken={accessToken} specUrl={demoSpecUrl} />
      </TabPane>

      <TabPane tab="All APIs" key="2">
        <OasUI accessToken={accessToken} specUrl={fullSpecUrl} />
      </TabPane>
    </Tabs>);
  }

  return renderOasUI();
};

ApiExplorer.propTypes = {
  history: PropTypes.object,
  accessToken: PropTypes.string,
};

export default (ApiExplorer);
