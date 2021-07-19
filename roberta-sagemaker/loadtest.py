import multiprocessing as mp
import numpy as np 
import datetime
import math
import time
import boto3
import botocore
import random

from essential_generators import DocumentGenerator
from sagemaker.serializers import JSONSerializer


sm_client = boto3.client(service_name='sagemaker')
runtime_sm_client = boto3.client(service_name='sagemaker-runtime')

#MME endpoint
endpoint_name = 'roberta-multimodel-endpoint2021-07-07-16-35-13'

gen = DocumentGenerator()
gen.init_word_cache(5000)
gen.init_sentence_cache(5000)
content_type = "application/json" 
client_times = []
errors_list = []
errors = 0


target_model = "roberta-base-0.tar.gz"
test_data = {"text": gen.sentence()}
jsons = JSONSerializer()
payload = jsons.serialize(test_data)

response = runtime_sm_client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType=content_type,
        TargetModel=target_model,
        Body=payload)

#print(response)
res = response['Body'].read()
#print(res)

