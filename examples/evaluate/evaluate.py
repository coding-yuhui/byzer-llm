import time
import json
import random
from enum import Enum
import pandas as pd
from pandas import DataFrame
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from byzerllm.utils.basic_llm_utils import (
    MessageRole,
    ChatMessage,
    ChatMessages,
    from_message_dicts,
    to_message_dicts
)


class QuestionCategory(Enum):
    INTENTION = "用户意图分类"
    SQL = "SQL"
    CHART_ANALYSIS = "Chart 图表分析"
    GOAL_REPORT = "目标总结"
    QUERY_SPEC_GEN = "QuerySpec 生成"
    QUERY_SPEC_ANALYSIS = "QuerySpec 理解"
    METRIC_RECOMMEND = "指标推荐"
    METRIC_ANALYSIS = "指标分析"
    UNKNOWN = "Unknown"


@dataclass
class Question:
    category: Union[str, QuestionCategory] = QuestionCategory.UNKNOWN
    messages: List[ChatMessage] = field(default_factory=list)
    raw_messages: Optional[str] = ""
    answer: Optional[str] = ""
    extra: Optional[dict] = field(default_factory=dict)
    gen_prompt: Optional[str] = ""
    gen_questions: Optional[str] = ""

    def set_answer(self, answer: str):
        self.answer = answer

    def to_dict(self) -> dict:
        _category = self.category
        if isinstance(self.category, QuestionCategory):
            _category = self.category.value
        return {
            "category": _category,
            "messages": json.dumps(to_message_dicts(self.messages), ensure_ascii=False, indent=2),
            "raw_messages": self.raw_messages if len(self.raw_messages) > 0 else self.to_common_chat_str(),
            "answer": self.answer,
            "gen_prompt": self.gen_prompt,
            "gen_questions": self.gen_questions,
        }

    def to_messages_dicts(self) -> List[dict]:
        return to_message_dicts(self.messages)

    def to_common_chat_str(
            self,
            role_mapping: Optional[Dict[str, str]] = None,
            **kwargs
    ) -> str:
        system_convert_to_user: bool = kwargs.get("system_convert_to_user", True)
        last_message_is_assistant: bool = kwargs.get("last_message_is_assistant", True)

        role_mapping = {
            "user": "User",
            "assistant": "Assistant",
        } if role_mapping is None else role_mapping

        new_messages = []
        user_role_mapping = role_mapping.get(MessageRole.USER, "User")
        assistant_role_mapping = role_mapping.get(MessageRole.ASSISTANT, "Assistant")

        for item in self.messages:
            role, content = item.role, item.content
            if role == MessageRole.SYSTEM:
                if system_convert_to_user:
                    new_messages.extend([f"{user_role_mapping}:{content}", f"{assistant_role_mapping}:OK\n"])
                else:
                    new_messages.append(content)
                continue
            else:
                new_messages.append(f"{role_mapping.get(role, role)}:{content}")

        # Make sure the last message is assistant
        if new_messages[-1].find(assistant_role_mapping) < 0 and last_message_is_assistant:
            new_messages.append(f"{assistant_role_mapping}:\n\n")

        return "\n".join(new_messages)


def load_data(file_path: str) -> List[Question]:
    data = pd.read_excel(file_path)
    # data = data.dropna()
    # data = data.drop_duplicates()
    q_list: List[Question] = []
    for i, r in data.iterrows():
        # category = str(r['category'])
        # input_data = str(r['input'])
        raw_input_data = str(r['raw_input'])

        try:
            messages = from_message_dicts(json.loads(raw_input_data))
            q_list.append(Question(category=QuestionCategory.UNKNOWN, messages=messages))
        except Exception as e:
            print(f"failed to convert to messages: {e}")
            continue

    print(f"load [{len(q_list)}] data from {file_path}")

    return q_list


def load_question_data_from_df(
        data: DataFrame,
        dropna: bool = False,
        drop_duplicates: bool = False
) -> List[Question]:
    # data = data.dropna()
    # data = data.drop_duplicates()
    q_list: List[Question] = []
    for i, r in data.iterrows():
        # category = str(r['category'])
        # input_data = str(r['input'])
        raw_input_data = str(r['raw_input'])

        q_list.append(Question(QuestionCategory.UNKNOWN, from_message_dicts(json.loads(raw_input_data))))

    print(f"load [{len(q_list)}] data from df")

    return q_list


def load_question_data(
        file_path: str,
        dropna: bool = False,
        drop_duplicates: bool = False
) -> List[Question]:
    data = pd.read_excel(file_path)
    if dropna:
        data = data.dropna()
    if drop_duplicates:
        data = data.drop_duplicates()
    q_list: List[Question] = []
    for i, r in data.iterrows():
        category = str(r['category'])
        messages = str(r['messages'])
        raw_messages = str(r['raw_messages'])
        answer = str(r['answer'])
        gen_questions = str(r['gen_questions'])

        q_list.append(
            Question(
                category=category,
                messages=from_message_dicts(json.loads(messages)),
                raw_messages=raw_messages,
                answer=answer,
                gen_questions=gen_questions
            )
        )

    print(f"load [{len(q_list)}] questions data from {file_path}")

    return q_list


def questions_to_dataframe(
        questions: List[Question],
        dropna: bool = False,
        drop_duplicates: bool = False
) -> pd.DataFrame:
    data = [question.to_dict() for question in questions]
    df = pd.DataFrame(data)
    if dropna:
        df = df.dropna()
    if drop_duplicates:
        df = df.drop_duplicates()
    return df


def transform_intention_data(questions: List[Question]) -> List[Question]:
    keyword = """USER's intention"""
    table_name_prefix = "Table Name:"
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        first_content = messages[0].content
        if first_content is not None and keyword in first_content:
            q.category = QuestionCategory.INTENTION
            q_c += 1
            if first_content is not None and table_name_prefix in first_content:
                messages[0].content = first_content[:first_content.find(table_name_prefix)] + "\n"

    print(f"transform [{q_c}] intention data")

    return questions


def transform_chart_analysis_data(questions: List[Question]) -> List[Question]:
    keyword = "Available Chart Types"
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        if messages[0].content is not None and messages[0].content.find(keyword) > 0:
            q.category = QuestionCategory.CHART_ANALYSIS
            q_c += 1

    print(f"transform [{q_c}] chart analysis data")

    return questions


def transform_query_spec_data(questions: List[Question]) -> List[Question]:
    q_analysis = 0
    q_gen = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        chat_str = q.to_common_chat_str()

        if chat_str.find('MetricQuerySpec') > 0 and chat_str.find('请遵循下面的规则，对用户问题和数据结果总结') > 0:
            q.category = QuestionCategory.QUERY_SPEC_ANALYSIS
            q_analysis += 1
        elif chat_str.find('MetricQuerySpec') > 0:
            q.category = QuestionCategory.QUERY_SPEC_GEN
            q_gen += 1

    print(f"transform [{q_gen}] QuerySpec gen data")

    print(f"transform [{q_analysis}] QuerySpec analysis data")

    return questions


def transform_sql_data(questions: List[Question]) -> List[Question]:
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        search_keywords = [
            "写一条Spark SQL回答用户问题",
            "写一条SQL来回答问题",
            "Please write a Spark SQL"
        ]

        for msg in messages:
            content = msg.content
            if content is not None and 'SQL' in content:
                if any(keyword in content for keyword in search_keywords):
                    q.category = QuestionCategory.SQL
                    q_c += 1
                    break

    print(f"transform [{q_c}] SQL data")

    return questions


def transform_goal_report_data(questions: List[Question]) -> List[Question]:
    """转换目标总结类数据"""
    keyword = "目标总结报告"
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        if messages[0].content is not None and messages[0].content.find(keyword) > 0:
            q.category = QuestionCategory.GOAL_REPORT
            q_c += 1

    print(f"transform [{q_c}] goal report data")

    return questions


def transform_metric_recommend_data(questions: List[Question]) -> List[Question]:
    """转换指标推荐类数据"""
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        for msg in messages:
            content = msg.content
            if content is None:
                continue
            if "已知系统Zen中有统计指标" in content or "It is known that system ZEN has the following metrics" in content:
                q.category = QuestionCategory.METRIC_RECOMMEND
                q_c += 1

    print(f"transform [{q_c}] metric recommend data")

    return questions


def transform_metric_analysis_data(questions: List[Question]) -> List[Question]:
    """转换指标分析类数据"""
    q_c = 0
    for q in questions:
        messages = q.messages

        if q.category != QuestionCategory.UNKNOWN:
            continue

        if messages and len(messages) <= 0:
            continue

        search_keywords = [
            "Please analyze the reasons for the recent fluctuations/rise/decline of the metric",
            "对指标进行归因分析后，得到如下信息",
            "根据归因分析结果，我们可以得出以下结论",
            "【Start Time】和【End Time】"
        ]

        for msg in messages:
            content = msg.content
            if content is not None and any(keyword in content for keyword in search_keywords):
                q.category = QuestionCategory.METRIC_ANALYSIS
                q_c += 1
                break

    print(f"transform [{q_c}] metric analysis data")

    return questions


def convert_to_zh_data(input_file: str = "./question_v17.xlsx", output_file: str = None):
    """转换、清理原始数据"""

    df = pd.read_excel(input_file)

    category_col, messages_col = [], []

    bad_user_question = [
        "null",
        "Null",
        "NULL",
        "nihao",
        "你好",
        "xxxx",
        "1",
        "zouc"
    ]

    exist_user_question = []

    for index, row in df.iterrows():
        category = str(row['category'])
        input_data = str(row['input'])
        raw_input_data = str(row['raw_input'])

        if input_data.find("English") >= 0 or input_data.find("english") >= 0:
            continue

        if category == "用户意图分类":
            messages_json = json.loads(raw_input_data)
            system_content = messages_json[0]['content']
            exist_table_name = system_content.find("Table Name")
            if exist_table_name > 0:
                messages_json[0]['content'] = system_content[:exist_table_name].strip()
                raw_input_data = json.dumps(messages_json, ensure_ascii=False, indent=2)
            last_content = messages_json[-1]['content']
            if last_content:
                user_q = last_content[len("""Give suggestion of options provided. 
Based on user input:"""):].strip()
                if (user_q == ""
                        or user_q in bad_user_question
                        or user_q in exist_user_question
                ):
                    continue
                exist_user_question.append(user_q)

        category_col.append(category)
        messages_col.append(raw_input_data)

    df_new = pd.DataFrame({"category": category_col, "messages": messages_col})

    df_new.drop_duplicates(ignore_index=True)

    return save_df_to_excel(df_new, output_file)


def convert_to_evaluate_data(raw_data: str, output_file: str = None):
    """
    从原始数据集抽取评测使用的数据，每个分类抽取20条
    """
    from byzerllm.utils import generate_instruction_from_history

    df = pd.read_excel(raw_data)

    data_dict = {
        "用户意图分类": {"messages": []},
        "Chart 图表分析": {"messages": []},
        "QuerySpec 生成": {"messages": []},
        "QuerySpec 理解": {"messages": []},
        "SQL": {"messages": []},
        "目标总结": {"messages": []},
        "指标推荐": {"messages": []},
        "指标分析": {"messages": []}
    }

    for index, row in df.iterrows():
        category = str(row['category'])
        raw_input_data = str(row['messages'])

        if category in data_dict:
            data_dict[category]["messages"].append(raw_input_data)

    # 循环字典并打乱消息顺序
    for k, v in data_dict.items():
        random.shuffle(v["messages"])
        v["selected_messages"] = random.sample(v["messages"], 20)

    category_col, messages_col, messages_str_col = [], [], []
    for category, value in data_dict.items():
        selected_messages = value['selected_messages']
        category_col.extend([category] * len(selected_messages))
        messages_col.extend(selected_messages)
        for msg in selected_messages:
            messages_str_col.append(generate_instruction_from_history("", json.loads(msg)))

    df = pd.DataFrame({
        "category": category_col,
        "messages": messages_col,
        "messages_str": messages_str_col,
    })

    return save_df_to_excel(df, output_file)


def load_evaluate_data(raw_data: str):
    """
    加载评测使用的数据集，每个分类20条
    """
    df = pd.read_excel(raw_data)

    data_dict = {
        "用户意图分类": {"messages": []},
        "Chart 图表分析": {"messages": []},
        "QuerySpec 生成": {"messages": []},
        "QuerySpec 理解": {"messages": []},
        "SQL": {"messages": []},
        "目标总结": {"messages": []},
        "指标推荐": {"messages": []},
        "指标分析": {"messages": []},
    }

    for index, row in df.iterrows():
        category = str(row['category'])
        raw_input_data = str(row['messages'])

        if category in data_dict:
            msg = json.loads(raw_input_data)
            data_dict[category]["messages"].append(msg)

    return data_dict


def save_df_to_excel(df: DataFrame, output_file: str = None) -> str:
    # 创建一个 Workbook 对象
    workbook = Workbook()
    worksheet = workbook.active

    # 添加标题行
    worksheet.append(list(df.columns))

    # 将 DataFrame 写入工作表
    for i, r in df.iterrows():
        worksheet.append(list(r))

    # 设置标题行的字体样式和对齐方式
    font = Font(bold=True)
    alignment = Alignment(horizontal='center', vertical='center')
    for cell in worksheet[1]:
        cell.font = font
        cell.alignment = alignment

    # 设置输入列和输出列的对齐方式和自动换行
    data_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)
    for r in worksheet.iter_rows(min_row=2, min_col=2, max_col=6):
        for cell in r:
            cell.alignment = data_alignment

    # 调整输入列和输出列的宽度
    worksheet.column_dimensions['A'].best_fit = True
    worksheet.column_dimensions['B'].width = 100
    worksheet.column_dimensions['C'].width = 100

    # 使用 auto_filter 方法添加筛选
    worksheet.auto_filter.ref = 'A:A'

    # 设置首行冻结，这将使首行保持可见，而其余的内容可以滚动
    worksheet.freeze_panes = "A2"  # "A2" 是冻结的首行下的第一行

    # 保存 Excel 文件
    output_file = f"data/output_{int(time.time())}.xlsx" if output_file is None else output_file
    workbook.save(filename=output_file)

    print(f"save [{len(df)}] data to [{output_file}] done!")

    return output_file
