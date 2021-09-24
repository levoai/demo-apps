/*
 * Copyright 2021 Levo, Inc.
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

import React, { useEffect } from "react";
import { Button } from "antd";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { getUserReportsAction } from "../../actions/vehicleActions";
import responseTypes from "../../constants/responseTypes";
import UserReports from "../../components/userReports/userReports";
import "./userReports.css";

const UserReportsContainer = (props) => {
  const { history, accessToken, getUserReports } = props;
  const [userReports, setUserReports] = React.useState([]);

  useEffect(() => {
    const callback = (res, data) => {
      if (res === responseTypes.SUCCESS) {
        setUserReports(data)
      } 
    };
    
    getUserReports({ callback, accessToken });

  }, [accessToken, getUserReports]);
  
  return (
    <div> 
      <div className="user-reports__header">
        <h1> Service Request Records </h1>
        <Button className="user-reports__backdash-button"
          type="primary"
          onClick={() => history.push(`/dashboard`)}
          key="back-button">
            Back to Dashboard
        </Button>
      </div>

      <div>
      <UserReports userReports={userReports} />
      </div>
    </div>
  );
};

const mapStateToProps = ({ userReducer: { accessToken } }) => {
  return { accessToken };
};

const mapDispatchToProps = {
  getUserReports: getUserReportsAction,
};

UserReportsContainer.propTypes = {
  accessToken: PropTypes.string,
  getUserReports: PropTypes.func,
  history: PropTypes.object,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(UserReportsContainer);

