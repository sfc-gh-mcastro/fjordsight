-- Script to check and modify network policies for FjordSight PoC

-- First, let's see what network policies exist
SHOW NETWORK POLICIES;

-- Check current user's role and privileges
SELECT CURRENT_ROLE();
SELECT CURRENT_USER();

-- Show account parameters related to network policies
SHOW PARAMETERS LIKE 'NETWORK_POLICY%' IN ACCOUNT;

-- Check if there are any network policies applied to your user
DESCRIBE USER mcastro;

-- Alternative: Check network policies on the account level
-- SHOW PARAMETERS LIKE '%NETWORK%' IN ACCOUNT;
