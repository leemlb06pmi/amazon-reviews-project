import os
import logging

from datetime import datetime
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator

from google.cloud import storage
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator
from kaggle.rest import ApiException
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
import shutil

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow")
#BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_multi')
    

def upload_to_gcs(bucket):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    api = KaggleApi()
    api.authenticate()
    
    client = storage.Client()
    bucket = client.bucket(bucket)

    ds = api.dataset_list(search="cynthiarempel")[0]
    file_result = api.dataset_list_files(ds.ref)
    failed_list = []

    for i in file_result.files:
        file_name = i
        try:
            print(f"downloading {file_name}")
            api.dataset_download_file(f"{ds.ref}", f"{i}")
            shutil.unpack_archive(f"{i}.zip", file_name)
            blob = bucket.blob(f"reviews/{file_name}")
            print(f"uploading {file_name}")
            blob.upload_from_filename(f"{AIRFLOW_HOME}/{file_name}")
        except ApiException:
            print(f"{file_name} python call failed")
            failed_list.append(file_name)        
        finally:
            try:
                print(f"removing file {file_name}")
                os.remove(f"{AIRFLOW_HOME}/{file_name}.zip")
                os.remove(f"{AIRFLOW_HOME}/{file_name}")
            except FileNotFoundError:
                pass

default_args = {
    "owner": "airflow",
    "start_date": datetime(2022,9,15),
    "depends_on_past": False,
    "retries": 1      
}

# NOTE: DAG declaration - using a Context Manager (an implicit way)
with DAG(
    dag_id="kag_to_gcs_dag",
    schedule_interval= None,
    default_args=default_args,
    catchup=True,
    max_active_runs=1,
) as dag:
    
    local_to_gcs_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            #"local_file":f"{AIRFLOW_HOME}/final_list.csv",
        },
    )

    check_list_task = BashOperator(
        task_id="check_list_task",
        bash_command="ls"
    )

    # download_raw_list_task = BashOperator(
    #     task_id="download_raw_list_task",
    #     bash_command=f"kaggle datasets files -v cynthiarempel/amazon-us-customer-reviews-dataset > {AIRFLOW_HOME}/raw_files.csv"
    # )

    # cleanup_list_task = PythonOperator(
    #     task_id="cleanup_list_task",
    #     python_callable=cleanup_list,
    #     op_kwargs={
    #         "raw_list": f"{AIRFLOW_HOME}/raw_files.csv"
    #     }   
    # )

    # bigquery_external_table_task = BigQueryCreateExternalTableOperator(
    #     task_id="bigquery_external_table_task",
    #     table_resource={
    #         "tableReference": {
    #             "projectId": PROJECT_ID,
    #             "datasetId": BIGQUERY_DATASET,
    #             "tableId": "external_table",
    #         },
    #         "externalDataConfiguration": {
    #             "sourceFormat": "PARQUET",
    #             "sourceUris": [f"gs://{BUCKET}/raw/{OUTPUT_FILE}"],
    #         },
    #     }
    # )

    # cleanup_local = BashOperator(
    #     task_id="cleanup_local",
    #     bash_command=f"rm {AIRFLOW_HOME}/{OUTPUT_FILE}"
    # )

    #download_dataset_task >> local_to_gcs_task >> cleanup_local

    #download_raw_list_task >> cleanup_list_task >> check_list_task

    local_to_gcs_task
    
