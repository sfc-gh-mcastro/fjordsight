-- Raw Data Tables for FjordSight PoC
-- These tables store the unprocessed data from various sources

USE DATABASE FJORDSIGHT_POC;
USE SCHEMA RAW_DATA;

-- Raw sensor data from MQTT streams
CREATE OR REPLACE TABLE RAW_SENSOR_DATA (
    TIMESTAMP TIMESTAMP_NTZ,
    FARM_LOCATION VARCHAR(100),
    LATITUDE FLOAT,
    LONGITUDE FLOAT,
    SENSOR_TYPE VARCHAR(50),
    VALUE FLOAT,
    UNIT VARCHAR(20),
    QUALITY VARCHAR(20),
    DEVICE_ID VARCHAR(100),
    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    -- Add clustering for better query performance
    CLUSTER BY (DATE_TRUNC('hour', TIMESTAMP), FARM_LOCATION, SENSOR_TYPE)
);

-- Raw ERP data (feed inventory, production metrics)
CREATE OR REPLACE TABLE RAW_ERP_DATA (
    TIMESTAMP TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    DATA_TYPE VARCHAR(50), -- 'feed_inventory', 'production_metrics', etc.
    LOCATION VARCHAR(100),
    FEED_QUANTITY_KG FLOAT,
    FISH_COUNT INT,
    AVERAGE_WEIGHT_KG FLOAT,
    GROWTH_RATE_PERCENT FLOAT,
    MORTALITY_RATE FLOAT,
    SOURCE_SYSTEM VARCHAR(50),
    CLUSTER BY (DATE_TRUNC('day', TIMESTAMP), DATA_TYPE, LOCATION)
);

-- Raw external data (weather, oceanographic data from Marketplace)
CREATE OR REPLACE TABLE RAW_EXTERNAL_DATA (
    TIMESTAMP TIMESTAMP_NTZ,
    DATA_SOURCE VARCHAR(100), -- 'openweather', 'noaa_oceanographic', etc.
    LOCATION VARCHAR(100),
    DATA_TYPE VARCHAR(50),
    DATA_JSON VARIANT,
    INGESTION_TIME TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CLUSTER BY (DATE_TRUNC('day', TIMESTAMP), DATA_SOURCE, LOCATION)
);

-- Create streams for real-time processing
CREATE OR REPLACE STREAM SENSOR_DATA_STREAM ON TABLE RAW_SENSOR_DATA;
CREATE OR REPLACE STREAM ERP_DATA_STREAM ON TABLE RAW_ERP_DATA;
CREATE OR REPLACE STREAM EXTERNAL_DATA_STREAM ON TABLE RAW_EXTERNAL_DATA;

-- Create stages for data loading
CREATE OR REPLACE STAGE SENSOR_DATA_STAGE
    FILE_FORMAT = JSON_FORMAT;

CREATE OR REPLACE STAGE ERP_DATA_STAGE
    FILE_FORMAT = CSV_FORMAT;

-- Add some sample data for demonstration
INSERT INTO RAW_SENSOR_DATA VALUES
    ('2024-01-15 10:00:00', 'North Atlantic Site', 60.5, 5.3, 'water_temp', 12.5, 'celsius', 'good', 'north_atlantic_site_water_temp_1001', CURRENT_TIMESTAMP()),
    ('2024-01-15 10:00:00', 'North Atlantic Site', 60.5, 5.3, 'oxygen', 8.9, 'mg/L', 'good', 'north_atlantic_site_oxygen_1002', CURRENT_TIMESTAMP()),
    ('2024-01-15 10:00:00', 'North Atlantic Site', 60.5, 5.3, 'ph', 7.6, 'pH', 'good', 'north_atlantic_site_ph_1003', CURRENT_TIMESTAMP()),
    ('2024-01-15 10:00:00', 'Fjord Site Alpha', 61.2, 6.1, 'water_temp', 11.8, 'celsius', 'good', 'fjord_site_alpha_water_temp_2001', CURRENT_TIMESTAMP()),
    ('2024-01-15 10:00:00', 'Fjord Site Alpha', 61.2, 6.1, 'oxygen', 9.2, 'mg/L', 'good', 'fjord_site_alpha_oxygen_2002', CURRENT_TIMESTAMP()),
    ('2024-01-15 10:00:00', 'Deep Water Beta', 59.8, 4.9, 'water_temp', 13.1, 'celsius', 'warning', 'deep_water_beta_water_temp_3001', CURRENT_TIMESTAMP());

INSERT INTO RAW_ERP_DATA (DATA_TYPE, LOCATION, FEED_QUANTITY_KG, FISH_COUNT, AVERAGE_WEIGHT_KG, GROWTH_RATE_PERCENT, MORTALITY_RATE, SOURCE_SYSTEM) VALUES
    ('feed_inventory', 'North Atlantic Site', 2500, 0, 0, 0, 0, 'SAP_ERP'),
    ('production_metrics', 'North Atlantic Site', 0, 10000, 4.2, 3.1, 0.02, 'Production_System'),
    ('feed_inventory', 'Fjord Site Alpha', 2200, 0, 0, 0, 0, 'SAP_ERP'),
    ('production_metrics', 'Fjord Site Alpha', 0, 9800, 4.1, 3.0, 0.025, 'Production_System'),
    ('feed_inventory', 'Deep Water Beta', 2800, 0, 0, 0, 0, 'SAP_ERP'),
    ('production_metrics', 'Deep Water Beta', 0, 10200, 4.3, 3.4, 0.018, 'Production_System');
