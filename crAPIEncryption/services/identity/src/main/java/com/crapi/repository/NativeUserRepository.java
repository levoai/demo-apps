/**
 * @author Levo.ai
 */
package com.crapi.repository;

import java.sql.Statement;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;

import org.json.JSONArray;
import org.json.JSONObject;

public class NativeUserRepository {

    private final String DB_HOST = System.getenv("DB_HOST");
    private final String DB_PORT = System.getenv("DB_PORT");
    private final String DB_NAME = System.getenv("DB_NAME");
    private final String DB_USER = System.getenv("DB_USER");
    private final String DB_PASSWORD = System.getenv("DB_PASSWORD");

    private final String DB_URL = "jdbc:postgresql://" + DB_HOST + ":" + DB_PORT + "/" + DB_NAME;

    private Connection conn = null;

    private JSONArray convertToJSON(ResultSet resultSet) throws Exception {
        JSONArray jsonArray = new JSONArray();

        while (resultSet.next()) {
            final int total_rows = resultSet.getMetaData().getColumnCount();
            JSONObject obj = new JSONObject();

            for (int i = 0; i < total_rows; i++) {
                obj.put(resultSet.getMetaData().getColumnLabel(i + 1)
                        .toLowerCase(), resultSet.getObject(i + 1));
            }
            jsonArray.put(obj);
        }

        return jsonArray;
    }

    private String JSONArrayToString(final JSONArray jsonArray) {
        String response = "";

        if (jsonArray.length() == 1) {
            // Remove array notation if only 1 element
            response = jsonArray.getJSONObject(0).toString(4);
        } else if (jsonArray.length() > 1) {
            response = jsonArray.toString(4);
        }

        return response;
    }

    public NativeUserRepository() {
        try {
            conn = DriverManager.getConnection(DB_URL, DB_USER, DB_PASSWORD);
        } catch (SQLException e) {
            System.out.println(e.getMessage());
        }
    }

    public String findUserByNumber(String number) {
        String response = "";
        if (conn == null) {
            return response;
        }

        // Allow SQLi here by using a native query
        final String SQL = "SELECT * FROM user_login u WHERE u.number = '" + number + "'";
        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(SQL);
            response = JSONArrayToString(convertToJSON(rs));
        } catch (Exception e) {
            System.out.println(e.getMessage());
        }

        return response;
    }
}
