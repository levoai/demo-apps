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

import React from "react";
import { Table } from "antd";



const UserReports = ({ userReports }) => {

  const columns = [
    {
      key: "report-id",
      render: (value, record) => record.id,
      title: "Report ID",
    },
    {
      key: "mechanic-info",
      render: (value, record) => (
        <div>
          <div> Email: {record.mechanic.user.email} </div>
          <div> Phone: {record.mechanic.user.number} </div>
        </div>
      ),
      title: "Mechanic Info",
    },
    {
      key: "vehicle-info",
      render: (value, record) => (
        <div>
          <div> VIN: {record.vehicle.vin} </div>
          <div> Owner Email: {record.vehicle.owner.email} </div>
          <div> Owner Phone: {record.vehicle.owner.number} </div>
        </div>
      ),
      title: "Vehicle Info",
    },
    {
      key: "problem",
      render: (value, record) => (
        <div>
          <div> {record.created_on} </div>
          <div> {record.problem_details} </div>
        </div>
      ),
      title: "Issues",
    },
    {
      key: "status",
      render: (value, record) => (
        <div>
          <div> {record.status} </div>
        </div>
      ),
      title: "Status",
    },
  ];

  return <Table
    rowKey="id"
    columns={columns}
    dataSource={userReports}
    pagination={false}
  />;
};

export default (UserReports);
