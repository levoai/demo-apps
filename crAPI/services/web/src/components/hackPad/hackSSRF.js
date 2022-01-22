import React from "react";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import { message, Card, Row, Form, Input, Select, Button } from "antd";

import { APIService, requestURLS } from "../../constants/APIConstant";

const HackSSRF = ({ accessToken }) => {

    const mechanicCode = ["TRAC_MECH1", "TRAC_MECH2"];
    const problemDetails = "My car has engine trouble, and I need urgent help!";
    const vinNo = "0BZCX25UTBJ987271";
    const mechanicAPI = "http://localhost:8000/workshop/api/mechanic/receive_report";

    const [ApiResponse, setApiResponse] = React.useState("");

    function handleResponse(response) {
        setApiResponse(response);
    }

    function contactMechanic(values) {
        const postUrl =
            APIService.PYTHON_MICRO_SERVICES + requestURLS.CONTACT_MECHANIC;

        const headers = {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        };
        
        fetch(postUrl, {
            headers,
            method: "POST",
            body: JSON.stringify({
                mechanic_code: values.mechanic_code,
                problem_details: values.problem_details,
                vin: values.vin,
                mechanic_api: values.mechanic_api,
                repeat_request_if_failed: values.repeat_request_if_failed,
                number_of_repeats: values.number_of_repeats,
            }),
        }).then((response) => response.text())
            .then(handleResponse)
            .catch((err) => {
                setApiResponse("Error Processing Request")
                message.error("Unable to POST Contact Mechanic API Endpoint!");
            });
    }

    const onFinish = (values) => {
        contactMechanic(values);
      };

    return (
        <>
            <Card title="Server Side Request Forgery Exploit">
                <Row>
                    <span>
                        The `Contact Mechanic` API endpoint takes a URL as an input.
                        <br/>
                        This input is used directly by the API implementation
                        without sanitization or validation. 
                        <br/>
                        You can exploit this input using, SSRF techniques and get access to internal sensitive data.
                        <br/> <br/>
                        Try <b> changing this URL </b> to access Google Compute Engine Meta Data APIs, or other internal resources.
                    </span>
                </Row>
                <Row className="hackcard__info" >
                    
                    <Form
                        name="ContactMechanic"
                        labelCol={{ span: 64 }}
                        labelAlign="left"
                        autoComplete="off"
                        initialValues={{
                            mechanic_api: mechanicAPI, mechanic_code: mechanicCode[0],
                            number_of_repeats: 0, repeat_request_if_failed: false, 
                            vin: vinNo, problem_details: problemDetails
                        }}
                        onFinish={onFinish}
                    >
                        <Form.Item
                            name="mechanic_api"
                            label="Mechanic API URL"
                            rules={[{ required: true }, { type: 'url', warningOnly: true }, { type: 'string', min: 6 }]}
                            defaultValue={mechanicAPI}
                        >
                            <Input style={{ width: 500 }} allowClear />
                        </Form.Item>
                        
                        <Form.Item name="mechanic_code" label="Mechanic Code">
                            <Select>
                                <Select.Option value={mechanicCode[0]}>{mechanicCode[0]}</Select.Option>
                                <Select.Option value={mechanicCode[1]}>{mechanicCode[1]}</Select.Option>
                            </Select>
                        </Form.Item>

                        <Form.Item
                            name="number_of_repeats"
                            label="Number of Repeats"
                        >
                            <Input style={{ width: 500 }} disabled={true} />
                        </Form.Item>

                        <Form.Item
                            name="repeat_request_if_failed"
                            label="Repeat Request If Failed"
                        >
                            <Input style={{ width: 500 }} disabled={true} />
                        </Form.Item>

                        <Form.Item
                            name="vin"
                            label="VIN"
                        >
                            <Input style={{ width: 500 }} disabled={true} />
                        </Form.Item>

                        <Form.Item
                            name="problem_details"
                            label="Problem Details"
                            rules={[{ required: true }, { type: 'string', min: 1 }]}
                        >
                            <Input style={{ width: 500 }} allowClear />
                        </Form.Item>

                        <Form.Item>
                            <Button type="primary" htmlType="submit">Submit</Button>
                        </Form.Item>
                        
                    </Form>
                    
                </Row>

                <Row>
                    <Input.TextArea
                        disabled={true}
                        style={{ width: 700 }}
                        bordered={"true"}
                        size={"large"}
                        autoSize={{minRows:10, maxRows:100}}
                        value={ApiResponse}>
                    </Input.TextArea>
                </Row>

            </Card>

        </>
    );
    
}


const mapStateToProps = ({ userReducer: { accessToken } }) => {
    return { accessToken };
};

HackSSRF.propTypes = {
    accessToken: PropTypes.string,
};

export default connect(mapStateToProps)(HackSSRF);