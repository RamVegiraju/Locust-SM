#
# run command: locust --host=localhost:8000
#

import os
import json
import time
import boto3
import gevent
import inspect
import numpy as np
from locust import HttpUser, task
from locust.env import Environment
from botocore.config import Config
from locust.log import setup_logging
from locust import User, TaskSet, task, events
from locust.contrib.fasthttp import FastHttpUser
from locust.stats import stats_printer, stats_history
from locust import HttpUser, task, events, between, constant, constant_pacing
from locust.runners import STATE_STOPPING, STATE_STOPPED, STATE_CLEANUP, WorkerRunner, STATE_RUNNING

run_logs_dir = 'run-logs/'

def stopwatch(func):
    def wrapper(*args, **kwargs):
        previous_frame = inspect.currentframe().f_back
        _, _, task_name, task_func_name, _ = inspect.getframeinfo(previous_frame)
        task_func_name = task_func_name[0].split('.')[-1].split('(')[0]

        self_here = args[0]

        start = time.time()
        result = None

        try:

            result = func(*args, **kwargs)
            total = int((time.time() - start) * 1000)

        except Exception as e:
            events.request_failure.fire(request_type=task_name,
                                        name=task_func_name,
                                        response_time=total,
                                        response_length=len(result),
                                        exception=e)
        else:
            _ = result
            events.request_success.fire(request_type=task_name,
                                        name=task_func_name,
                                        response_time=total,
                                        response_length=len(result))
        return result
    return wrapper

class ProtocolClient:
    def __init__(self, host):

        self.endpoint_name = host.split('/')[-1]
        self.region = 'us-east-1'
        self.content_type = 'application/json'
        self.payload = json.dumps({"text": "Matthias Tomczak 220,000. 89.2% of inhabitants"})
        self.target_model = "roberta-base-0.tar.gz"
        
        print(self.endpoint_name)
 
        boto3config = Config(
            retries={
                'max_attempts': 100,
                'mode': 'standard'
            }
        )
        self.sagemaker_client = boto3.client('sagemaker-runtime',
                                             config=boto3config,
                                             region_name=self.region)

    @stopwatch
    def sagemaker_client_invoke_endpoint(self):
        response = self.sagemaker_client.invoke_endpoint(
            EndpointName=self.endpoint_name,
            Body=self.payload,
            ContentType=self.content_type,
            TargetModel=self.target_model
        )
        response_body = response["Body"].read()
        return response_body

class ProtocolLocust(FastHttpUser):
    abstract = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = ProtocolClient(self.host)
        self.client._locust_environment = self.environment

class ProtocolTasks(TaskSet):
    @task
    def custom_protocol_boto3(self):
        self.client.sagemaker_client_invoke_endpoint()

class ProtocolUser(ProtocolLocust):
    wait_time = constant(0)
    tasks = [ProtocolTasks]
