import json
import pandas as pd 
import pandas_gbq

from env import *
from google.oauth2 import service_account
import logging 
import requests 
import ollama   


def postToSlack(exception, llm_suggestion):
    webhook_url = SLACK_URL

    failure_payload = {"text": f"🚨 Data Upload: Failure - {exception}."}
    requests.post(webhook_url, json=failure_payload)
    
    llm_payload = {"text": f"LLM Suggestion for fix:\n```{llm_suggestion}```"}
    requests.post(webhook_url, json=llm_payload)


def llmSchemaValidation(df, schema_definition):
    
    client = ollama.Client()
    model = 'gpt-oss:120b-cloud'
    prompt = f"""
You are a data quality assistant. Given the schema definition and observed dataset profile:

1. Identify schema for any drift violations
2. Suggest possible root causes

Provide your analysis in a structured format in no longer than 2 paragraphs. 
Be concise and focus on actionable insights. In your response, be sure to include the validation status as a key value pair 
with the key as "validation_status" and value as either "PASS" or "FAIL". Return your response in a structured JSON format.

Dataset profile:
{df.dtypes} 
Schema definition file: {schema_definition}

""".strip()
    
    resp = client.generate(model=model, prompt= prompt)
    clean_resp = resp.response

    return clean_resp

def main(file_name):
    
        #Load data into pandas dataframe
        sample_data = pd.read_csv(file_name)
        
        #Load schema definition
        with open('schema.json', 'r') as f:
            schema_definition = json.load(f)
        
        #Validate dataframe schema using LLM
        llm_response = llmSchemaValidation(sample_data, schema_definition)

        #Load LLM response into JSON and check validation status
        response_data = json.loads(llm_response)
        
        validation_status = response_data.get("validation_status")

        #If validation fails, post to Slack and raise exception. If it passes, load data into BigQuery
        if validation_status == "FAIL":
            # Convert dict back to string for Slack if your function requires a string
            slack_message = json.dumps(response_data, indent=2)
            postToSlack("🚨 Schema drift detected", slack_message)
            raise Exception("Schema drift detected. Check Slack for details.")
        
        else: 
            try:

                credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
                
                pandas_gbq.to_gbq(sample_data, 
                                'dev.cars', 
                                project_id=GCP_PROJECT_ID,
                                table_schema=schema_definition, 
                                credentials=credentials,
                                if_exists='append')
                    
            except Exception as e:
                # Catching non-schema errors (Network, Auth, Quotas)
                postToSlack("❌ BigQuery Ingestion Failed", str(e))
                logging.error(f"BigQuery ingestion failed: {e}")

if __name__ == "__main__":
    main('sample2.csv')
