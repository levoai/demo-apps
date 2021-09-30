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

import { useEffect } from "react";
import { connect } from "react-redux";
import PropTypes from "prop-types";
import { logInUserAction } from "../../actions/userActions";
import responseTypes from "../../constants/responseTypes";

const AutoLoginContainer = (props) => {
  const { history, logInUser } = props;

  const queryParams = new URLSearchParams(window.location.search)
  const route = queryParams.get("route")
  const email = queryParams.get("email")
  const password = queryParams.get("password")
  const path = (route === null) ? "/dashboard" : route

  useEffect(() => {
    
    const callback = (res, data) => {
      if (res === responseTypes.SUCCESS) {
        history.push(path);
      } else {
        history.push("/login")
      }
    };
  
    logInUser({ email, password, callback });
  }, [email, password, path, logInUser, history]);

  return null;
};

const mapDispatchToProps = {
  logInUser: logInUserAction,
};

AutoLoginContainer.propTypes = {
  logInUser: PropTypes.func,
  history: PropTypes.object,
  isLoggedIn: PropTypes.bool,
};

export default connect(null, mapDispatchToProps)(AutoLoginContainer);
