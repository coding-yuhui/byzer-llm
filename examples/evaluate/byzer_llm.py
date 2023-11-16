from typing import Optional, Union
from byzerllm.utils.client import ByzerLLM, LLMRequest, LLMRequestExtra

llm = ByzerLLM()


def chat(
        messages: Union[list, str, LLMRequest] = None,
        model: str = "azure_openai",
        verbose: Optional[bool] = False,
        **kwargs
):
    llm_req_extra = LLMRequestExtra(system_msg="", user_role="", history=[])
    llm_req = LLMRequest(
        instruction="",
        max_length=kwargs.get("max_length", 4096),
        temperature=kwargs.get("temperature", 0.01),
        top_p=kwargs.get("top_p", 0.7),
        extra_params=llm_req_extra
    )
    if isinstance(messages, str):
        llm_req.instruction = messages
    elif isinstance(messages, LLMRequest):
        llm_req = messages
    elif isinstance(messages, list):
        llm_req.extra_params.history = messages

    if verbose:
        print(f"【Byzer -> {model}】: {llm_req}")

    try:
        return llm.chat(model, request=llm_req)[0].output
    except Exception as e:
        failed_msg = f"request failed: {e}"
        print(failed_msg)
        return failed_msg
