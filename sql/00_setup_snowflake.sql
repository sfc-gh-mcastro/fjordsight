-- Use elevated privileges
USE ROLE ACCOUNTADMIN;

-- -- Create a dedicated role, service user, database, and warehouse
CREATE OR REPLACE ROLE aicollege;

CREATE OR REPLACE USER mlops_user
  TYPE = SERVICE 
  DEFAULT_ROLE = aicollege 
  COMMENT = 'Service user for FjordSight';

-- Grant role to service user and your standard user
GRANT ROLE aicollege TO USER mlops_user;
GRANT ROLE aicollege TO USER mcastro;

-- Create database and warehouse
CREATE OR REPLACE DATABASE aicollege;

CREATE OR REPLACE WAREHOUSE aicollege
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 300;

-- Grant required permissions
GRANT USAGE, OPERATE ON WAREHOUSE aicollege TO ROLE aicollege;
GRANT ALL ON DATABASE aicollege TO ROLE aicollege;
GRANT ALL ON SCHEMA aicollege.public TO ROLE aicollege;
GRANT CREATE STAGE ON SCHEMA aicollege.public TO ROLE aicollege;
GRANT SELECT ON FUTURE TABLES IN SCHEMA aicollege.public TO ROLE aicollege;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA aicollege.public TO ROLE aicollege;

-- Create a staging area for uploads
CREATE OR REPLACE STAGE aicollege.public.setup;
GRANT READ,WRITE ON STAGE aicollege.public.setup TO ROLE aicollege;

-- -- Create a staging area for notebooks
-- CREATE OR REPLACE STAGE aicollege.public.notebooks;
-- GRANT READ,WRITE ON STAGE aicollege.public.notebooks TO ROLE aicollege;


ALTER USER mlops_user SET DEFAULT_ROLE = AICOLLEGE;

-- --Keys
ALTER USER mlops_user SET RSA_PUBLIC_KEY='
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv4rMkun1DecPXhLKQxwD
H0llvK7PYNkOx+3F0vsIo2euzMCvlIyZ795VKFn/m6D6YksBra9IgrrUgLSz/ZQy
Y2oyvEXhoq8UFXT8DY/kyFnC8u6EryfLV0pGtUHQayjxjW51kbegx5posLq16L9f
mDRYNQ+06chPj3cnT/pM9rJfWT7mGpgR7wXWnUd9ucZPl4I7eWp1rdiZwztFzcE3
wAtK+eByPnbKbSOWFD4tIDvdwrjTBkD6ewPW/rRhgh24KwNa+e5utNO0wfdIluL7
jLLetiffWfSB8PeC31yo2LglzjjnxGbWSvPbPdXwQQ/5Eq6olbu7iPwbyA6YNLEy
qQIDAQAB
 -----END PUBLIC KEY-----';

 USE ROLE ACCOUNTADMIN;
--Create the network policy
CREATE NETWORK POLICY ALLOW_DEMO
  ALLOWED_IP_LIST = ('92.220.67.138')
  COMMENT = 'Restrict access to SageMaker IPs for MLOps HOL';
  -- Assign the policy to the service user only (NOT to the full account)
ALTER USER mlops_user SET NETWORK_POLICY = ALLOW_DEMO;
-- Confirm it's set correctly
DESC USER mlops_user;
