import ray

from typing import List

from byzer_llm import chat
from evaluate import (
    Question,
    QuestionCategory,
    load_data,
    save_df_to_excel,
    transform_intention_data,
    transform_chart_analysis_data,
    transform_query_spec_data,
    transform_sql_data,
    transform_goal_report_data,
    transform_metric_analysis_data,
    transform_metric_recommend_data,
    questions_to_dataframe
)

ray.init("ray://172.16.10.245:10001", namespace="default", ignore_reinit_error=True)


def run_cleaning_pipeline(file_path: str) -> List[Question]:
    questions = load_data(file_path)
    questions = transform_intention_data(questions)
    questions = transform_chart_analysis_data(questions)
    questions = transform_query_spec_data(questions)
    questions = transform_sql_data(questions)
    questions = transform_goal_report_data(questions)
    questions = transform_metric_recommend_data(questions)
    questions = transform_metric_analysis_data(questions)
    df = questions_to_dataframe(questions)
    save_df_to_excel(df, "data/old/question_v19_3.xlsx")
    return questions


def main():
    question_list = run_cleaning_pipeline("data/old/question_v18_1.xlsx")

    chart_analysis_questions: List[Question] = []
    intention_questions: List[Question] = []
    query_spec_gen_questions: List[Question] = []
    query_spec_analysis_questions: List[Question] = []
    goal_report_questions: List[Question] = []
    metric_recommend_questions: List[Question] = []
    metric_analysis_questions: List[Question] = []
    sql_questions: List[Question] = []

    for q in question_list:

        if q.category == QuestionCategory.CHART_ANALYSIS:
            chart_analysis_questions.append(q)

        if q.category == QuestionCategory.INTENTION:
            intention_questions.append(q)

        if q.category == QuestionCategory.QUERY_SPEC_GEN:
            query_spec_gen_questions.append(q)

        if q.category == QuestionCategory.QUERY_SPEC_ANALYSIS:
            query_spec_analysis_questions.append(q)

        if q.category == QuestionCategory.GOAL_REPORT:
            goal_report_questions.append(q)

        if q.category == QuestionCategory.METRIC_ANALYSIS:
            metric_analysis_questions.append(q)

        if q.category == QuestionCategory.METRIC_RECOMMEND:
            metric_recommend_questions.append(q)

        if q.category == QuestionCategory.SQL:
            sql_questions.append(q)

    model = "azure_openai"
    final_answers = []
    for i, q in enumerate(intention_questions):
        answer = chat(model=model, verbose=False, messages=q.to_messages_dicts())
        print(f"question-{i}: {answer}")
        q.set_answer(answer)
        final_answers.append(q)
    save_df_to_excel(questions_to_dataframe(final_answers), "data/intention_openai_answer_1.xlsx")


if __name__ == '__main__':
    main()
