import React, { useEffect, useCallback } from "react";
import {
  Input,
  Row,
  Col,
  Card,
  Modal,
  Table,
} from "antd";
import { getMapUrl } from "../../utils";
import PropTypes from "prop-types";
import { connect } from "react-redux";
import responseTypes from "../../constants/responseTypes";
import { getVehiclesAction, refreshLocationActionV2 } from "../../actions/vehicleActions";
import "./hackCard.css"


const { Search } = Input;


const HackLocation = ({ accessToken, getVehicles, refreshLocation }) => {
    const [vehicles, setVehicles] = React.useState([])
    useEffect(() => {
        const callback = (res, data) => {
            if (res === responseTypes.SUCCESS) {
                setVehicles(data)
            } else {
                setVehicles([])
            }
        };

        getVehicles({ callback, accessToken });
    }, [accessToken, getVehicles]);
    
    const defaultLocation = {"carId" : 0, "fullName" : "", "vehicleLocation" : {"id" : 0, "latitude" : "0", "longitude" : "0"} };
    const [vehicleLocation, setLocation] = React.useState(defaultLocation);
    
    const handleGetLocation = useCallback((carId) => {
        const callback = (res, data) => {
            if (res === responseTypes.SUCCESS) {
                setLocation(data)
            } else { 
                Modal.error({
                    title: data
                });
                setLocation(defaultLocation)
            }
        };
        
        refreshLocation({ callback, accessToken, carId });
    }, [accessToken, refreshLocation, defaultLocation]);

    return (
        <>
            <Card title="Vehicle Location Info Exploit">
                <Row>
                    <span>
                        You can get the location info for any vehicle in crAPI,
                        if you know the UUID of the vehicle. You can refer to the
                        GitHub page to see <a href="https://github.com/levoai/demo-apps/blob/main/crAPI/docs/user-asset-info.md#users-vechicle-uuid"
                            target="_blank" rel="noopener noreferrer">
                            documented UUIDs</a> of other vehicles.
                        <br />
                        This is a serious vulnerability that allows unauthorized
                        location info disclosure!!
                        <br/> <br/>
                        <p> Try it now! </p>
                    </span>
                </Row>
                <Row className="hackcard__info" >
                    <Col span={12}>
                        <VehiclesTable vehicles={vehicles} />
                    </Col>
                    
                    <Col span={8} offset={4}>
                        <Search
                            style={{ width: 350 }}
                            placeholder="Enter vehicle UUID?"
                            allowClear
                            bordered="true"
                            enterButton
                            onSearch={value => {
                                if (value) { handleGetLocation(value) }
                            }
                            }
                        />
                        <br/> <br/>
                        <p> Vehicle Owner Name: <b>{vehicleLocation.fullName}</b> </p>
                        <iframe
                            className="map-iframe"
                            height="360"
                            width="350"
                            src={getMapUrl(
                                vehicleLocation.vehicleLocation.latitude,
                                vehicleLocation.vehicleLocation.longitude
                            )}
                            title="Map"
                        />
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
    refreshLocation: refreshLocationActionV2,
    getVehicles: getVehiclesAction,
};

HackLocation.propTypes = {
    accessToken: PropTypes.string,
    getVehicles: PropTypes.func,
    refreshLocation: PropTypes.func,
};

export default connect(mapStateToProps, mapDispatchToProps)(HackLocation);

const VehiclesTable = ({vehicles}) => {
  
    const vehicleColumns = [
        {
          key: "uuid",
          render: (value, record) => record.uuid,
          title: "Vehicle UUID",
        },
        {
          key: "model",
          render: (value, record) => (
            <div>
              <div> Model: {record.model.model} </div>
              <div> Make: {record.model.vehiclecompany.name} </div>
              <div> Year: {record.year} </div>
            </div>
          ),
          title: "Model",
        },
        {
          key: "vin",
          render: (value, record) => (
            <div>
              <div> VIN: {record.vin} </div>
            </div>
          ),
          title: "VIN#",
        },
      ];
    
    return <Table
        rowKey="id"
        title={() => 'The vehicles you own:'}
        columns={vehicleColumns}
        dataSource={vehicles}
        bordered={true}
        pagination={false}
    />;
  };

  