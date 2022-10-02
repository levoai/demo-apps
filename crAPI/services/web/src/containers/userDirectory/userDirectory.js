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
import { Button, Modal } from "antd";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { getUserDirectoryAction } from "../../actions/userActions";
import responseTypes from "../../constants/responseTypes";
import UserDirectory from "../../components/userDirectory/userDirectory";
import "./userDirectory.css";

const UserDirectoryContainer = (props) => {
  const { history, accessToken, getUserDirectory } = props;
  const [userDirectory, setUserDirectory] = React.useState([]);

  useEffect(() => {
    const callback = (res, data) => {
      if (res === responseTypes.SUCCESS) {
        setUserDirectory(data)
      } else {
        Modal.error({ title: data });
        setUserDirectory([])
      }
    };
    
    getUserDirectory({ callback, accessToken });

  }, [accessToken, getUserDirectory]);
  
  return (
    <div> 
      <div className="user-directory__header">
        <h1> All Registered Users </h1>
        <Button className="user-directory__backdash-button"
          type="primary"
          onClick={() => history.push(`/dashboard`)}
          key="back-button">
            Back to Dashboard
        </Button>
      </div>

      <div>
      <UserDirectory userDirectory={userDirectory} />
      </div>
    </div>
  );
};

const mapStateToProps = ({ userReducer: { accessToken } }) => {
  return { accessToken };
};

const mapDispatchToProps = {
  getUserDirectory: getUserDirectoryAction,
};

UserDirectoryContainer.propTypes = {
  accessToken: PropTypes.string,
  getUserDirectory: PropTypes.func,
  history: PropTypes.object,
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(UserDirectoryContainer);

