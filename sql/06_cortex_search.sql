--USE ROLE ACCOUNTADMIN;
-- Based on https://github.com/sfc-gh-mcastro/data-agent-hol-college-of-ai/


-- Create AICOLLEGE.PUBLIC.TRANSCRIPTS stage to transcripts and semantic yaml file
CREATE STAGE IF NOT EXISTS AICOLLEGE.FJORDSIGHT_POC.TRANSCRIPTS
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );

-- Grant privileges to the AICOLLEGE role
GRANT READ, WRITE ON STAGE AICOLLEGE.FJORDSIGHT_POC.TRANSCRIPTS TO ROLE aicollege;





--Cortex search notebook
-- Create AICOLLEGE.PUBLIC.TRANSCRIPTS stage to transcripts and semantic yaml file
CREATE STAGE IF NOT EXISTS AICOLLEGE.FJORDSIGHT_POC.notebooks
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );

-- Grant privileges to the AICOLLEGE role
GRANT READ, WRITE ON STAGE AICOLLEGE.FJORDSIGHT_POC.notebooks TO ROLE aicollege;

-- copy notebooks into Snowflake & configure runtime settings
CREATE OR REPLACE NOTEBOOK aicollege.FJORDSIGHT_POC.Video_Agent_Cortex_Search
FROM '@aicollege.FJORDSIGHT_POC.notebooks'
MAIN_FILE = 'Video_Agent_Cortex_Search.ipynb'
WAREHOUSE = aicollege
QUERY_WAREHOUSE = aicollege;

----

SELECT 
    --REGEXP_REPLACE(RELATIVE_PATH,'Aqua_NOR\\.pdf$','') AS CUSTOMER_NAME,
    RELATIVE_PATH,
    SNOWFLAKE.CORTEX.PARSE_DOCUMENT(      --> Use Snowflake's Parse Document function
        '@AICOLLEGE.FJORDSIGHT_POC.TRANSCRIPTS',
        RELATIVE_PATH,
        OBJECT_CONSTRUCT('mode','layout') --> Use layout mode
    ) AS RAW_TEXT
FROM DIRECTORY('@AICOLLEGE.FJORDSIGHT_POC.TRANSCRIPTS') f
WHERE
  RELATIVE_PATH NOT IN (SELECT RELATIVE_PATH FROM PARSED_TRANSCRIPTS);
