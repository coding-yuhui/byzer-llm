import copy
import ray
import json

from byzer_llm import chat
from byzerllm.utils.basic_llm_utils import (
    ChatMessage,
    MessageRole
)
from evaluate import (
    load_question_data,
    save_df_to_excel,
    questions_to_dataframe
)

ray.init("ray://172.16.10.245:10001", namespace="default", ignore_reinit_error=True)

QUESTION_GEN_V1 = """I want you to act as a curious questioner and come up with a new question based \
 on the original problem and context. 

Step by step, what additional information do you need to know to better understand the \
 situation? What other perspectives or angles could be explored? How might this issue \
 impact different groups of people? Use your creativity and critical thinking skills to \
 craft a thought-provoking question that will inspire further discussion and exploration.

Finally, generate at least 10 new questions, each with no more than 15 words. Generate in Chinese. \
 You must strictly use the following JSON format to return:
 ```
 [
    {

        "new_question": "here is new question",
        "new_question_answer": "generate answers based on new questions and contexts"
    }
    ...
 ]
 ```

Original Question: %s
Context: %s 
New Questions: 
"""

context_str = """你是Kyligence Copilot，使用中文回答问题，提供指标数据的分析能力。
    Each reply MUST choose one of following options by USER's intention:
    * [JUST_CHAT] - Free chat if topic is not about metrics
    * [SEND_TO_FEISHU] - Send/Share metrics info to feishu
    * [CREATE_DASHBOARD] - Create a default dashboard
    * [JUST_CREATE_TASK] - Create a Feishu task
    * [CHANGE_METRIC] - Change topic metric if user asks to CHANGE
    * [ACCUMULATED_DATA_OF_METRIC] - Use SQL to analyze metrics, which is very useful when you need to accumulated metrics data
    * [CALCULATION_OF_METRIC] - Use SQL to analyze metrics, Useful when you need to perform group statistical analysis on indicators, or sort
    * [ANALYSIS_WITH_VISUALIZATION] - Analyze metrics and show with visualization
    * [DESCRIBE_METRIC_SCHEMA] - Show metrics table schema if user requests data structure

    You must choose one as an answer, and answer does not need any other explanation or descriptive content.
"""

# all_questions = load_question_data("data/question_v20.xlsx", drop_duplicates=True)
#
# intention_questions = []
# for q in all_questions:
#     if q.category == QuestionCategory.INTENTION.value:
#         intention_questions.append(q)
#
# save_df_to_excel(questions_to_dataframe(intention_questions))

intention_questions = load_question_data("data/output_1699929713.xlsx")
new_intentions_questions = []

INPUT_PREFIX = """Give suggestion of options provided. 
Based on user input:"""

for i, q in enumerate(intention_questions):
    messages = q.messages
    final_gen_prompt = None
    # gen new question, prepare gen prompt
    try:
        if messages and messages[-1].content:
            old_q_content = messages[-1].content[len(INPUT_PREFIX):].strip()
            prompt = QUESTION_GEN_V1 % (
                old_q_content,
                messages[0].content
            )
            # print(final_gen_prompt)
            answer = chat(prompt, model="azure_openai", temperature=0.9, verbose=False)
            new_questions = json.loads(answer)
            for idx, new_q_content in enumerate(new_questions):
                new_q = copy.deepcopy(q)
                new_q.messages.pop()
                new_q.messages.append(ChatMessage(
                    role=MessageRole.USER,
                    content=INPUT_PREFIX + " " + new_q_content["new_question"]
                ))
                new_q.set_answer(new_q_content["new_question_answer"])
                new_intentions_questions.append(new_q)
                print(f"generate the [{idx}] question based on question [{i}]")
    except Exception as e:
        print(f"failed to generate new question for the [{i}] question: {e}")
        continue

print(f"gen [{len(new_intentions_questions)}] intention questions.")

if len(new_intentions_questions) > 0:
    q_df = questions_to_dataframe(new_intentions_questions)
    save_df_to_excel(q_df, "data/intention_question_v3.xlsx")
