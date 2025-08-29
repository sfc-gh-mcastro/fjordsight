

---

### **Product Requirements Document: Project FjordSight PoC**

**Author:** FjordSight's, Snowflake Elite Principal Solution Engineer
**Audience:** FjordSight's & Snowflake Joint PoC Team
**Version:** 1.0
**Date:** August 29th , 2025

**1.0 Executive Summary & PoC Vision**

* **1.1 The Problem:** Briefly summarize FjordSight's "triple threat" and how data silos are the root cause.  
* **1.2 The Vision:** Articulate the "after" state. Describe a future where FjordSight operates a "Digital Farm," a central command center providing a holistic, real-time view of operations from egg to harvest. Emphasize the shift from reactive problem-solving to proactive, AI-driven optimization.  
* **1.3 PoC Goal:** State that this PoC will prove that Snowflake is the only platform capable of realizing this vision by unifying complex IT/OT data, delivering predictive insights with AI/ML, and empowering all users with secure, governed data access.

**2.0 Target Personas & Solutions**

Create a Markdown table with the following columns: Persona, Core Pains, and PoC Solution & Value. Populate it for:

* Data Engineer  
* Data Scientist  
* Data Analyst / Business User (Sales & Operations Managers)

**3.0 Functional Requirements & Demo Storyboard**

This section must outline a compelling, narrative-driven demo flow, broken into three distinct vignettes.

* **Vignette 1: The Unified IT/OT Data Foundation (Audience: Data Engineers, Ops Managers)**  
  * **Objective:** Demonstrate the seamless ingestion and unification of siloed IT and OT data.  
  * **Steps:**  
    1. \[cite\_start\]Show the current fragmented state (mentioning  
       Ignition, ERPs, SQL on-prem, Excel).  
    2. Architect and justify the chosen MQTT ingestion pattern. \[cite\_start\]  
       **Recommend the most robust, scalable, and near-real-time option from the documents (e.g., Mqtt \- Kafka \- Kafka connector/snowpipe streaming \- snowflake or Mqtt \- snowpipe streaming \- snowflake) and briefly state why it is superior to batch-oriented options**.  
    3. \[cite\_start\]Show live OT sensor data (e.g., water temperature, oxygen levels) streaming into Snowflake and being harmonized with IT data (e.g., feed inventory from an ERP) in a single  
       HARMONIZED table.  
    4. \[cite\_start\]Highlight the automation and reduced maintenance using Dynamic Tables or Streams & Tasks.  
* **Vignette 2: Proactive Environmental Threat Mitigation (Audience: Data Scientists, Biologists)**  
  * **Objective:** Showcase Snowflake's integrated AI/ML capabilities to solve a high-value biological problem.  
  * **Steps:**  
    1. Using the unified data from Vignette 1, show how a Data Scientist can easily build, train, and deploy a predictive model using Snowpark for Python or Snowflake Cortex.  
    2. The model's goal: A **Harmful Algal Bloom (HAB) Early Warning System**. \[cite\_start\]It should use real-time sensor data and enrich it with third-party oceanographic data from the Snowflake Marketplace.  
    3. Demonstrate the model's output: a risk score forecast for the next 48 hours.  
    4. \[cite\_start\]Showcase a Cortex Anomaly Detection function running on sensor data to identify subtle environmental changes that precede a bloom.  
* **Vignette 3: The AI-Powered Command Center (Audience: Data Analysts, Sales, Executives)**  
  * **Objective:** Demonstrate how unified data and AI insights are made accessible and actionable for business users.  
  * **Steps:**  
    1. \[cite\_start\]Present a  
       **Streamlit application** built natively in Snowflake, serving as the "Digital Farm Command Center".  
    2. The dashboard should visualize the real-time sensor data and the HAB risk score from the previous vignettes. Show an alert being triggered when the risk exceeds a threshold.  
    3. Pivot to the **AI Sales Co-Pilot**. Demonstrate a scenario where a "prediction error" occurs with a harvested salmon batch.  
    4. \[cite\_start\]The Streamlit app will take the mismatched volume as input and, using an ML model, instantly recommend the top 3 customers to call, ranked by profitability, historical preference, and risk, thus turning a potential loss into a maximized profit.

**4.0 PoC Technical Architecture**

* Provide a clear diagram of the proposed future-state architecture on Snowflake. It must include:  
  * **Data Sources:** (Ignition MQTT, ERPs, Excel, Marketplace).  
  * **Ingestion Layer:** (Snowpipe Streaming / Kafka Connector).  
  * **Storage & Processing Layer:** (Raw, Harmonized, and Analytics zones; Snowpark for ML, Cortex AI).  
  * **Consumption Layer:** (Streamlit, Power BI).

**5.0 Success Criteria & Business Impact KPIs**

Define the specific, measurable criteria for a successful PoC. Create a Markdown table with columns: Success Criterion, Measurement Method, and Business Impact (KPI). Include at least:

* Successful ingestion of MQTT data with \< 1-minute latency.  
* Deployment of a predictive HAB model with demonstrable accuracy.  
* A fully functional Streamlit application that visualizes real-time data and runs the AI Sales Co-Pilot.  
* \[cite\_start\]Link these technical wins to the KPIs from the Value Engineering exercise (e.g., Reduced Data Pipeline Maintenance Costs, Reduced Risk of Fish Mortality Events, Increased Revenue from Operational Yield Optimization).

---

* 