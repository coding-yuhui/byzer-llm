import ray
from ray import serve
from aviary.backend.server.run import llm_server,LLMApp 
import ray._private.usage.usage_lib
from typing import Union
import socket
import os
import base64

def _get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def _build_deepspeed_yaml(
        udfName:str,
        model_dir:str,
        num_gpus_per_worker:int=1,
):        
    model_id = udfName
    template = f"""deployment_config:
  max_concurrent_queries: 64  
  ray_actor_options:
      resources:
        master: 0.0001
model_config:
  batching: static
  model_id: {model_id}
  model_url: {model_dir}
  max_input_words: 800
  initialization:
    hf_model_id: {model_dir}
    initializer:
      type: DeepSpeed
      dtype: float16
      from_pretrained_kwargs:
        trust_remote_code: true
      use_kernel: true
      max_tokens: 1536  
    pipeline: transformers
  generation:
    max_input_words: 800
    max_batch_size: 18
    generate_kwargs:
      do_sample: true
      max_new_tokens: 512
      min_new_tokens: 16
      temperature: 0.7
      repetition_penalty: 1.1
      top_p: 0.8
      top_k: 5
    prompt_format:      
      system: "{{instruction}}\\n"
      assistant: "{{instruction}}\\n"
      trailing_assistant: "{{instruction}}\\n"
      user: "{{instruction}}\\n"
      default_system_message: "Below is an instruction that describes a task. Write a response that appropriately completes the request."
    stopping_sequences: []
scaling_config:
  num_workers: 4
  num_gpus_per_worker: 1
  num_cpus_per_worker: 1
  pg_timeout_s: 6000
""" 
    curr = os.path.expanduser("~")
    deploy_dir = os.path.join(curr,"byzer_model_deploy")
    deploy_file = os.path.join(deploy_dir,model_id)
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir) 

    if os.path.exists(deploy_file):
        os.remove(deploy_file)

    with open(deploy_file, "w") as f:
        f.write(template)

    return deploy_file   

def _build_devicemap_yaml(
        udfName:str,
        model_dir:str,
        num_gpus_per_worker:int=1,
):        
    model_id = udfName
    template = f"""deployment_config:
  max_concurrent_queries: 64  
  ray_actor_options:
      resources:
        master: 0.0001
model_config:
  batching: static
  model_id: {model_id}
  model_url: {model_dir}
  max_input_words: 800
  initialization:
    hf_model_id: {model_dir}
    initializer:
      type: DeviceMap
      dtype: bfloat16
      from_pretrained_kwargs:
        trust_remote_code: true
        use_cache: true
      use_bettertransformer: false
      torch_compile:
        backend: inductor
        mode: max-autotune
    pipeline: transformers
  generation:
    max_input_words: 800
    max_batch_size: 18
    generate_kwargs:
      do_sample: true
      max_new_tokens: 512
      min_new_tokens: 16
      temperature: 0.7
      repetition_penalty: 1.1
      top_p: 0.8
      top_k: 5
    prompt_format:      
      system: "{{instruction}}\\n"
      assistant: "{{instruction}}\\n"
      trailing_assistant: ""
      user: "{{instruction}}\\n"
      default_system_message: ""
    stopping_sequences: []
scaling_config:
  num_workers: 4
  num_gpus_per_worker: 1
  num_cpus_per_worker: 1
  pg_timeout_s: 6000
""" 
    curr = os.path.expanduser("~")
    deploy_dir = os.path.join(curr,"byzer_model_deploy")
    deploy_file = os.path.join(deploy_dir,model_id)
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir) 

    if os.path.exists(deploy_file):
        os.remove(deploy_file)

    with open(deploy_file, "w") as f:
        f.write(template)

    return deploy_file   
   
          

def build_model_serving(udfName,model_dir,num_gpus_per_worker:int=1):
    """Run the LLM Server on the local Ray Cluster

    Args:
        *models: A list of LLMApp objects or paths to yaml files defining LLMApps

    Example:
       run("models/")           # run all models in the models directory
       run("models/model.yaml") # run one model in the model directory
       run({...LLMApp})         # run a single LLMApp
       run("models/model1.yaml", "models/model2.yaml", {...LLMApp}) # mix and match
    """
    model_yaml = _build_devicemap_yaml(udfName,model_dir,num_gpus_per_worker=num_gpus_per_worker)
    print(f"the path of model_yaml[{model_dir}]: {model_yaml}")
    router, deployments, deployment_routes, app_names = llm_server([model_yaml])
    ray._private.usage.usage_lib.record_library_usage("aviary")
    model_id = [item for item in deployments.keys()][0]
    app = deployments[model_id]
    route = deployment_routes[model_id]
    app_name = app_names[model_id]

    available_port = _get_free_port()
    model_infer = serve.run(
            app,
            name=app_name,
            route_prefix=route,
            host="127.0.0.1",
            port=available_port,
            _blocking=False,
        )
    print(f"[{model_id}] [{app_name}] Model serving is running on 127.0.0.1:{available_port}",flush=True)
    return model_infer
        