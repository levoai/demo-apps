import React, { useCallback } from "react";
import {
  Input,
  Row,
  Col,
  Card,
  Modal,
} from "antd";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import responseTypes from "../../constants/responseTypes";
import { getServiceReportAction } from "../../actions/vehicleActions";
import UserReports from "../userReports/userReports";
import "./hackCard.css"


const { Search } = Input;

const HackServiceReport = ({ accessToken, getServiceReport }) => {

    const [svcReport, setReport] = React.useState([]);

    const handleGetReport = useCallback((reportID) => {
        const callback = (res, data) => {
            if (res === responseTypes.SUCCESS) {
                setReport([data])
            } else {
                Modal.error({
                    title: "Unable to get service report!"
                });
                setReport([])
            }
        };

        getServiceReport({ callback, accessToken, reportID });
    }, [accessToken, getServiceReport]);


    return (
        <>
            <Card title="Vehicle Service Report Exploit">
                <Row>
                    <span>
                        You can access anyone's service report by simply enumerating the ID of the report.
                        <br/>
                        You can see the reports you created in the Dashboard. Other user's reports are documented <a 
                        href="https://github.com/levoai/demo-apps/blob/main/crAPI/docs/user-asset-info.md#users-service-reports">
                            here. </a>
                        <br />
                        This is a serious vulnerability that allows unauthorized
                        info disclosure!!
                        <br/> <br/>
                        <p>Try enumerating other users reports now!</p>
                    </span>
                    
                </Row>
                <Row className="hackcard__info" >
                    <Col span={24}>
                        <Search
                            style={{ width: 250 }}
                            placeholder="Enter service report ID?"
                            allowClear
                            bordered={ true }
                            enterButton
                            onSearch={value => {
                                if (value) { handleGetReport(value) }
                            }
                            }
                        />
                        <br/> <br/>
                        <UserReports userReports={svcReport} />
                    </Col>
                    
                </Row>
            </Card>

        </>
    );
};

const mapStateToProps = ({ userReducer: { accessToken } }) => {
    return { accessToken };
};

const mapDispatchToProps = {
    getServiceReport: getServiceReportAction
};

HackServiceReport.propTypes = {
    accessToken: PropTypes.string,
    getServiceReport: PropTypes.func,
};

export default connect(mapStateToProps, mapDispatchToProps)(HackServiceReport);


  