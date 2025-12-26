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

import "./hackPad.css";

import { connect } from "react-redux";
import React from "react";
import PropTypes from "prop-types";
import {
  PageHeader,
  Button,
  Card,
  Row,
  Layout,
  Col,
} from "antd";
import ClipboardCopy from "../clipboardCopy/clipboardCopy";
import HackLocation from "./hackLocation.js"
import HackServiceReport from "./hackServiceReport";
import HackSSRF from "./hackSSRF";


const { Content } = Layout;


const HackPad = ({history, accessToken}) => {

  return (
    <div>
      <PageHeader
        className="hackpad__header"
        title="Welcome to Hack Pad!"
        extra={[
          <Button className="hackpad__header-backdash-button"
            type="primary"
            onClick={() => history.push(`/dashboard`)}
            key="back-button">
            Back to Dashboard
          </Button>
        ]}
      />

      <Content>
        <Row gutter={[40, 40]}>
          <Col span={24} key="description">
            <Card className="hackpad__header__description">
              <h1> Hack Pad allows you to actively hack crAPI. </h1>
              <h4>
                crAPI has several <a href="https://github.com/levoai/demo-apps/blob/main/crAPI/docs/challenges.md">
                  vulnerabilities. </a>
                Below exercises demonstrate exploiting these vulnerabilities.
              </h4>
              <div className="hackpad__header__token">
                <span className="hackpad__header__token__text"> This is your access token: </span>
                <ClipboardCopy copyText={accessToken} />
              </div>
            </Card>
          </Col>
        </Row>
      </Content>

      <Content className="hackpad__card">
        <HackServiceReport accessToken={accessToken} />
      </Content>

      <Content className="hackpad__card">
        <HackLocation accessToken={accessToken} />
      </Content>

      <Content className="hackpad__card">
        <HackSSRF accessToken={accessToken} />
      </Content>

    </div>
  );
};

const mapStateToProps = ({ vehicleReducer: { vehicles } }) => {
  return { vehicles };
};

HackPad.propTypes = {
  history: PropTypes.object,
  accessToken: PropTypes.string,
};

export default connect(mapStateToProps)(HackPad);
