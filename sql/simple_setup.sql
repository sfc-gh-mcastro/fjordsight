-- Simple FjordSight Schema Setup for existing database
-- Works with limited permissions

-- Use the existing database
USE DATABASE aicollege;

-- Create a simple schema for FjordSight (if permissions allow)
CREATE SCHEMA IF NOT EXISTS FJORDSIGHT_POC;
USE SCHEMA FJORDSIGHT_POC;

-- Create basic tables for demo
CREATE OR REPLACE TABLE FARM_SENSOR_DATA (
    TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    FARM_LOCATION VARCHAR(100),
    SENSOR_TYPE VARCHAR(50),
    VALUE FLOAT,
    UNIT VARCHAR(20),
    QUALITY VARCHAR(20)
);

CREATE OR REPLACE TABLE CUSTOMER_DATA (
    CUSTOMER_ID VARCHAR(100),
    CUSTOMER_NAME VARCHAR(200),
    CUSTOMER_TYPE VARCHAR(50),
    PROFITABILITY_TIER VARCHAR(20),
    RELATIONSHIP_SCORE FLOAT
);

-- Insert sample data
INSERT INTO FARM_SENSOR_DATA VALUES
    (CURRENT_TIMESTAMP(), 'North Atlantic Site', 'water_temp', 12.5, 'celsius', 'good'),
    (CURRENT_TIMESTAMP(), 'North Atlantic Site', 'oxygen', 8.9, 'mg/L', 'good'),
    (CURRENT_TIMESTAMP(), 'Fjord Site Alpha', 'water_temp', 11.8, 'celsius', 'good');

INSERT INTO CUSTOMER_DATA VALUES
    ('CUST_001', 'Nordic Seafood Restaurant Group', 'restaurant', 'HIGH', 4.5),
    ('CUST_002', 'Fjord Fish Distributors', 'distributor', 'MEDIUM', 4.0),
    ('CUST_003', 'Gourmet Market Chain', 'retailer', 'HIGH', 4.2);

SELECT 'FjordSight basic setup completed!' AS STATUS;
