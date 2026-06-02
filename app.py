import datetime
import json
import os
import re
import time
import random
from functools import lru_cache
from threading import Thread, Event, Lock
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import math
from sqlalchemy import func, and_
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'vue-project/src/assets')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
db = SQLAlchemy(app)
client = OpenAI(api_key="sk-de310ae824a84f25a95fcd4ff73f87d7", base_url="https://api.deepseek.com")
pending_tasks = {}


# 全局任务状态管理器（仅跟踪需要等待的异步任务）
class AsyncTaskManager:
    def __init__(self):
        self.tasks = {}  # 结构: {sub_id: {'status': 'processing/done', 'event': Event, 'result': ...}}
        self.lock = Lock()
        self.cleanup_interval = 3600  # 清理已完成任务的间隔（秒）

    def add_task(self, sub_id):
        """添加需要等待的异步任务"""
        with self.lock:
            if sub_id not in self.tasks:
                self.tasks[sub_id] = {
                    'status': 'processing',
                    'event': Event(),
                    'result': None,
                    'expire_time': datetime.datetime.now() + datetime.timedelta(seconds=self.cleanup_interval)
                }
            return self.tasks[sub_id]

    def get_task(self, sub_id):
        """获取任务状态"""
        with self.lock:
            return self.tasks.get(sub_id)

    def mark_done(self, sub_id, result):
        """标记任务完成"""
        with self.lock:
            if sub_id in self.tasks:
                self.tasks[sub_id]['status'] = 'done'
                self.tasks[sub_id]['result'] = result
                self.tasks[sub_id]['event'].set()

    def cleanup_expired_tasks(self):
        """清理过期任务（后台线程运行）"""
        while True:
            time.sleep(60)  # 每分钟检查一次
            with self.lock:
                now = datetime.datetime.now()
                expired_sub_ids = [
                    sub_id for sub_id, task in self.tasks.items()
                    if task['status'] == 'done' and now > task['expire_time']
                ]
                for sub_id in expired_sub_ids:
                    del self.tasks[sub_id]


# 初始化任务管理器和清理线程
task_manager = AsyncTaskManager()
cleanup_thread = Thread(target=task_manager.cleanup_expired_tasks, daemon=True)
cleanup_thread.start()


# =============================
# Scoring Criteria (英文精简版)
# =============================
@lru_cache(maxsize=2)
def get_scoring_criteria(task_type: int):
    task1_criteria = """
        [Task 1 Band Descriptors]

        TA (Task Achievement):
        9: Full data coverage + precise trend analysis
        7: Key features identified with minor omissions
        5: Missing significant data points
        3: Serious misinterpretation

        CC (Coherence & Cohesion):
        9: Seamless paragraph transitions
        7: Logical but mechanical linking
        5: Disjointed progression
        3: No paragraphing

        LR (Lexical Resource):
        9: Precise data verbs (plummet/surge)
        7: Appropriate academic vocabulary
        5: Basic terms repetition
        3: Template-dependent

        GRA (Grammatical Range):
        9: Error-free comparative structures
        7: Compound sentences with minor errors
        5: Simple sentences dominate
        3: Fragmented syntax"""

    task2_criteria = """
        [Task 2 Band Descriptors]

        TR (Task Response):
        9: Nuanced arguments + solid evidence
        7: Clear position with thin support
        5: Vague stance + weak examples
        3: Off-topic

        CC (Coherence & Cohesion):
        9: Natural transitions + referencing
        7: Formulaic but functional links
        5: Choppy connections
        3: No structure

        LR (Lexical Resource):
        9: Sophisticated academic phrases
        7: Correct terminology with slips
        5: Limited vocabulary
        3: Frequent spelling errors

        GRA (Grammatical Range):
        9: Masterful complex structures
        7: Controlled compound sentences
        5: Persistent basic errors
        3: No clause control"""

    return task1_criteria if task_type == 1 else task2_criteria


# =============================
# System Message Builder (英文系统消息)
# =============================
def build_system_message(task_type: int):
    """Build system role message in English"""
    criteria = get_scoring_criteria(task_type)
    return {
        "role": "system",
        "content": f"""Act as an official IELTS examiner. Follow these rules:
1. Scoring Criteria ({'Task 1' if task_type == 1 else 'Task 2'}):
{criteria}
2. Evaluation Requirements:
   - Provide constructive feedback using integer scores (1-9) for each criterion
   - Deliver evaluations in polished academic English
   - For every criterion:
    Begin with 1-2 positive observations
    Then highlight 2 specific, actionable improvements
   - Rigorously align with official band descriptors"""
    }


# =============================
# User Prompt Builder (英文用户提示)
# =============================
def build_user_prompt(essay: str, title: str, chart_data: str):
    """Build user prompt in English"""
    task_note = "(Chart Essay)" if chart_data else "(Argumentative Essay)"
    chart_section = f"\nChart Data Description: {chart_data}" if chart_data else ""
    return f"""Evaluate this IELTS essay {task_note}:
Title: {title}
{chart_section}
Essay Content:
{essay}

Output Format:
{'TA' if chart_data else 'TR'}: [score]
CC: [score]
LR: [score]
GRA: [score]
Evaluation: [Provide specific suggestions in academic English]"""


# =============================
# Response Parser (英文响应解析)
# =============================
def parse_response(response_text: str):
    """Parse API response text"""
    # Score extraction pattern
    score_pattern = r"(TA|TR|CC|LR|GRA):\s*(\d)"
    matches = re.findall(score_pattern, response_text)

    # Score mapping
    scores = {
        "coherence_cohesion": 0,
        "lexical_resource": 0,
        "grammatical_accuracy": 0
    }
    ta_score = tr_score = None

    # 解析逻辑
    for abbrev, score in matches:
        if abbrev == "TA":
            ta_score = int(score)
        elif abbrev == "TR":
            tr_score = int(score)
        elif abbrev == "CC":
            scores["coherence_cohesion"] = int(score)
        elif abbrev == "LR":
            scores["lexical_resource"] = int(score)
        elif abbrev == "GRA":
            scores["grammatical_accuracy"] = int(score)

    # 动态添加字段
    if ta_score is not None:
        scores["task_achievement"] = ta_score  # 安全新建字段
    elif tr_score is not None:
        scores["task_response"] = tr_score  # 安全新建字段
    else:
        raise ValueError("Missing task score")
    # Evaluation section parsing
    evaluation = re.split(r"Evaluation:", response_text, flags=re.IGNORECASE)[-1].strip()

    return {
        "scores": scores,
        "evaluation": evaluation
    }


def format_datetime(value):
    if value is None:
        return None
    return value.strftime('%Y-%m-%d %H:%M:%S')


def to_dict(instance):
    return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}


# 学生模型
class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# 教师模型
class Teacher(db.Model):
    teacher_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Class(db.Model):
    __tablename__ = 'class'
    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    classname = db.Column(db.String, nullable=False)
    creator_id = db.Column(db.Integer)


class Coursework(db.Model):
    __tablename__ = 'coursework'
    cw_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    review_set = db.Column(db.String)
    avg_score = db.Column(db.Float)


class Submission(db.Model):
    __tablename__ = 'submission'
    sub_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)
    sub_time = db.Column(db.DateTime)
    score = db.Column(db.Float)
    type = db.Column(db.String)
    completion_time = db.Column(db.Time)


class Bank(db.Model):
    __tablename__ = 'bank'
    bank_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_name = db.Column(db.String)
    bank_type = db.Column(db.String)
    location = db.Column(db.String)
    display_order = db.Column(db.Integer)


class BigQuestion(db.Model):
    __tablename__ = 'big_question'
    big_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_id = db.Column(db.Integer)
    type = db.Column(db.String, nullable=False)  # 题型：例如 "multiple_choice", "matching", "fill_in", "summary" 等
    question_description = db.Column(db.Text)
    start_number = db.Column(db.Integer)
    end_number = db.Column(db.Integer)
    if_nb = db.Column(db.Integer)  # 是否为非标题，依据业务需求


class SmallQuestion(db.Model):
    __tablename__ = 'small_questions'
    small_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    big_id = db.Column(db.Integer)
    question_number = db.Column(db.Integer)
    question_content = db.Column(db.Text)  # 小题题干/描述
    question_options = db.Column(db.Text)  # 存储 JSON 格式的选项（如果有），否则为空
    question_answer = db.Column(db.Text)  # 正确答案


class Answer(db.Model):
    __tablename__ = 'answer'
    answer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sub_id = db.Column(db.Integer)
    question_id = db.Column(db.Integer)  # 对应 small_questions.small_id
    user_answer = db.Column(db.Text)
    if_correct = db.Column(db.Boolean)


class PeerReview(db.Model):
    __tablename__ = 'peer_review'
    peer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reviewer_id = db.Column(db.Integer)
    reviewer_type = db.Column(db.String)
    student_id = db.Column(db.Integer)
    review_time = db.Column(db.DateTime)
    review_information = db.Column(db.Text)
    review_result = db.Column(db.String)
    sub_id = db.Column(db.Integer)
    is_anonymous = db.Column(db.Boolean)


class Resource(db.Model):
    __tablename__ = 'resource'
    resource_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_information = db.Column(db.Text)
    resource_type = db.Column(db.String)  # text/audio/video
    bank_id = db.Column(db.Integer)


class Matching(db.Model):
    __tablename__ = 'matching'
    matching_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reviewer_id = db.Column(db.Integer)
    cw_id = db.Column(db.Integer)
    student_id = db.Column(db.Integer)


class CwBank(db.Model):
    __tablename__ = 'cw_bank'
    bank_id = db.Column(db.Integer, primary_key=True)
    cw_id = db.Column(db.Integer, primary_key=True)


class StudentCourses(db.Model):
    __tablename__ = 'student_courses'
    student_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, primary_key=True)


class DetectionResults(db.Model):
    __tablename__ = 'detection_results'
    detection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_fake = db.Column(db.Boolean)
    confidence = db.Column(db.Integer)
    evaluation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    peer_id = db.Column(db.Integer)


# 创建数据库表
with app.app_context():
    db.create_all()


# 注册接口
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    user_type = data.get('user_type')  # 'student' 或 'teacher'
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 检查用户名和邮箱是否已存在
    if Student.query.filter((Student.username == username) | (Student.email == email)).first():
        return jsonify({'message': 'Username or email already exists (Student)'}), 400
    if Teacher.query.filter((Teacher.username == username) | (Teacher.email == email)).first():
        return jsonify({'message': 'Username or email already exists (Teacher)'}), 400
    # 根据用户类型创建用户
    if user_type == 'student':
        user = Student(username=username, email=email, password=generate_password_hash(password))
    elif user_type == 'teacher':
        user = Teacher(username=username, email=email, password=generate_password_hash(password))
    else:
        return jsonify({'message': 'Invalid user type'}), 400

    db.session.add(user)
    db.session.commit()
    print(check_password_hash(user.password, password))
    return jsonify({'message': 'User registered successfully'}), 201


# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_type = data.get('user_type')  # 'student' 或 'teacher'
    username_or_email = data.get('identifier')
    password = data.get('password')

    # 根据用户类型查询用户
    if user_type == 'student':
        user = Student.query.filter(
            (Student.username == username_or_email) | (Student.email == username_or_email)).first()
        userid = user.student_id
    elif user_type == 'teacher':
        user = Teacher.query.filter(
            (Teacher.username == username_or_email) | (Teacher.email == username_or_email)).first()
        userid = user.teacher_id
    else:
        return jsonify({'message': 'Invalid user type'}), 400

    # 验证用户和密码
    if not user:
        return jsonify({'message': 'Invalid username/email'}), 401
    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password'}), 401
    # 返回登录成功信息
    return (jsonify(
        {'message': f'Successfully logged in as {user_type}', 'user_type': user_type, 'username': user.username,
         'token': userid}), 200)


@app.route('/api/banks/<bank_type>', methods=['GET'])
def get_banks_grouped(bank_type):
    # 根据bank_type过滤数据
    banks = Bank.query.filter_by(bank_type=bank_type).all()

    # 使用集合去重，确保相同的location只显示一个卡片
    grouped = {}
    for bank in banks:
        a_part, b_part = bank.location.split(":") if ":" in bank.location else (bank.location, "")
        if a_part not in grouped:
            grouped[a_part] = []
        # 只添加唯一的b_part
        if b_part not in [item["b"] for item in grouped[a_part]]:
            grouped[a_part].append({
                "b": b_part,
                "bank_name": bank.bank_name,
                "display_order": bank.display_order
            })

    # 按a从大到小排序
    sorted_a = sorted(grouped.keys(), key=lambda x: int(x[1:]) if x[0] == 'a' else x, reverse=True)

    # 每个a下的b按从小到大排序
    for a in sorted_a:
        grouped[a] = sorted(grouped[a], key=lambda x: x["b"])

    return jsonify({"grouped": grouped, "sorted_a": sorted_a})


@app.route('/api/banks/<bank_type>/<a>', methods=['GET'])
def get_ab_banks(bank_type, a):
    # 获取所有a相同的数据
    banks = Bank.query.filter(
        Bank.location.startswith(f"{a}:"),  # 过滤a相同的数据
        Bank.bank_type == bank_type
    ).order_by(Bank.display_order).all()

    # 按b分组
    grouped = {}
    for bank in banks:
        _, b = bank.location.split(":")
        if b not in grouped:
            grouped[b] = []
        grouped[b].append({
            "bank_name": bank.bank_name,
            "display_order": bank.display_order
        })

    return jsonify(grouped)


@app.route('/api/bank-details/<bank_type>/<a>/<b>/<display_order>', methods=['GET'])
def get_bank_details(bank_type, a, b, display_order):
    # 查找符合条件的 Bank
    location = f"{a}:{b}"
    bank = Bank.query.filter_by(
        bank_type=bank_type,
        location=location,
        display_order=display_order
    ).first()

    if not bank:
        return jsonify({"error": "Bank not found"}), 404

    # 查找该 Bank 对应的 Resource
    resources = Resource.query.filter_by(bank_id=bank.bank_id).all()

    # 查找该 Bank 对应的 BigQuestion，并按 start_number 从小到大排序
    big_questions = BigQuestion.query.filter_by(bank_id=bank.bank_id).order_by(BigQuestion.start_number.asc()).all()

    # 为每个 BigQuestion 查找对应的 SmallQuestion，并按 question_number 从小到大排序
    big_questions_data = []
    for big_question in big_questions:
        small_questions = SmallQuestion.query.filter_by(big_id=big_question.big_id).order_by(
            SmallQuestion.question_number.asc()).all()
        big_questions_data.append({
            "big_id": big_question.big_id,
            "bank_id": big_question.bank_id,
            "type": big_question.type,
            "question_description": big_question.question_description,
            "start_number": big_question.start_number,
            "end_number": big_question.end_number,
            "if_nb": big_question.if_nb,
            "small_questions": [
                {
                    "small_id": small_question.small_id,
                    "big_id": small_question.big_id,
                    "question_number": small_question.question_number,
                    "question_content": small_question.question_content,
                    "question_options": small_question.question_options,
                    "question_answer": small_question.question_answer
                }
                for small_question in small_questions
            ]
        })

    # 返回 Bank、Resource、BigQuestion 和 SmallQuestion 数据
    return jsonify({
        "bank": {
            "bank_id": bank.bank_id,
            "bank_name": bank.bank_name,
            "location": bank.location,
            "display_order": bank.display_order
        },
        "resources": [
            {
                "resource_id": resource.resource_id,
                "resource_information": resource.resource_information,
                "resource_type": resource.resource_type
            }
            for resource in resources
        ],
        "big_questions": big_questions_data
    })


# 添加班级
@app.route('/api/class', methods=['POST'])
def add_class():
    data = request.json
    new_class = Class(classname=data['classname'], creator_id=data['creator_id'])
    db.session.add(new_class)
    db.session.commit()
    return jsonify({'class_id': new_class.class_id, 'classname': new_class.classname}), 201


# 删除班级
@app.route('/api/class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    class_to_delete = db.session.get(Class, class_id)
    if not class_to_delete:
        return jsonify({'message': 'Class not found'}), 404
    db.session.delete(class_to_delete)
    db.session.commit()
    return jsonify({'message': 'Class deleted'}), 200


# 获取当前教师创建的班级
@app.route('/api/classes/<int:teacher_id>', methods=['GET'])
def get_classes_by_teacher(teacher_id):
    classes = Class.query.filter_by(creator_id=teacher_id).all()
    class_list = [{'class_id': cls.class_id, 'classname': cls.classname} for cls in classes]
    return jsonify(class_list), 200


# 添加学生到班级
@app.route('/api/class/<int:class_id>/student', methods=['POST'])
def add_student_to_class(class_id):
    data = request.json
    student_id = data['student_id']
    # 检查学生是否已存在
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'message': 'Student not found'}), 404
    # 检查是否已关联
    existing = StudentCourses.query.filter_by(student_id=student_id, class_id=class_id).first()
    if existing:
        return jsonify({'message': 'Student already in class'}), 400
    # 添加关联
    new_association = StudentCourses(student_id=student_id, class_id=class_id)
    db.session.add(new_association)
    db.session.commit()
    return jsonify({'message': 'Student added to class'}), 201


# 从班级中删除学生
@app.route('/api/class/<int:class_id>/student/<int:student_id>', methods=['DELETE'])
def delete_student_from_class(class_id, student_id):
    association = StudentCourses.query.filter_by(student_id=student_id, class_id=class_id).first()
    if not association:
        return jsonify({'message': 'Student not found in class'}), 404
    db.session.delete(association)
    db.session.commit()
    return jsonify({'message': 'Student removed from class'}), 200


# 获取班级中的学生
@app.route('/api/class/<int:class_id>/students', methods=['GET'])
def get_students_in_class(class_id):
    students = db.session.query(Student).join(
        StudentCourses, Student.student_id == StudentCourses.student_id
    ).filter(StudentCourses.class_id == class_id).all()
    student_list = [{'student_id': s.student_id, 'username': s.username} for s in students]
    return jsonify(student_list), 200


# 搜索不在指定班级的学生
@app.route('/api/students/search/not_in_class', methods=['GET'])
def search_students_not_in_class():
    query = request.args.get('query')
    class_id = request.args.get('class_id')
    # 获取所有匹配查询的学生
    students = Student.query.filter(Student.username.like(f'%{query}%')).all()
    # 获取已经在班级中的学生ID
    students_in_class = db.session.query(StudentCourses.student_id).filter(StudentCourses.class_id == class_id).all()
    students_in_class_ids = [s.student_id for s in students_in_class]
    # 过滤掉已经在班级中的学生
    filtered_students = [s for s in students if s.student_id not in students_in_class_ids]
    student_list = [{'student_id': s.student_id, 'username': s.username} for s in filtered_students]
    return jsonify(student_list), 200


# 获取班级名称和学生人数
@app.route('/api/class/<int:class_id>', methods=['GET'])
def get_class(class_id):
    class_data = db.session.get(Class, class_id)
    if not class_data:
        return jsonify({'message': 'Class not found'}), 404
    student_count = StudentCourses.query.filter_by(class_id=class_id).count()
    return jsonify({'classname': class_data.classname, 'student_count': student_count}), 200


# 获取唯一的 location A
@app.route('/api/bank/unique_a', methods=['GET'])
def get_unique_a():
    bank_type = request.args.get('type')
    unique_a = db.session.query(
        func.substr(Bank.location, 1, func.instr(Bank.location, ':') - 1).label('a')
    ).filter(
        Bank.bank_type == bank_type
    ).distinct().all()
    unique_a = [a[0] for a in unique_a]
    return jsonify(unique_a), 200


# 获取唯一的 location B
@app.route('/api/bank/unique_b', methods=['GET'])
def get_unique_b():
    bank_type = request.args.get('type')
    location_a = request.args.get('a')
    unique_b = db.session.query(
        func.substr(Bank.location, func.instr(Bank.location, ':') + 1).label('b')
    ).filter(
        Bank.bank_type == bank_type,
        Bank.location.startswith(f'{location_a}:')
    ).distinct().all()
    unique_b = [b[0] for b in unique_b]
    return jsonify(unique_b), 200


# 获取唯一的 order 和对应的 bank_name 和 bank_id
@app.route('/api/bank/unique_order', methods=['GET'])
def get_unique_order():
    bank_type = request.args.get('type')
    location_a = request.args.get('a')
    location_b = request.args.get('b')
    unique_order = db.session.query(
        Bank.display_order,
        Bank.bank_name,
        Bank.bank_id
    ).filter(
        Bank.bank_type == bank_type,
        Bank.location == f'{location_a}:{location_b}'
    ).distinct().all()
    unique_order = [{'order': o[0], 'bank_name': o[1], 'bank_id': o[2]} for o in unique_order]
    return jsonify(unique_order), 200


@app.route('/api/coursework', methods=['POST'])
def create_coursework():
    data = request.json

    # 验证截止日期是否晚于当前时间
    if datetime.datetime.fromisoformat(data['deadline']) <= datetime.datetime.utcnow():
        return jsonify({'message': 'Deadline must be later than current time'}), 400

    # 验证互评数量是否合法
    review_set = data.get('review_set')
    if review_set:
        review_count = int(review_set.split(',')[0].split(':')[1].strip())
        student_count = StudentCourses.query.filter_by(class_id=data['class_id']).count()
        if review_count <= 0 or review_count >= student_count:
            return jsonify(
                {'message': 'Number of peer reviews must be greater than 0 and less than the number of students'}), 400

    # 创建作业
    new_coursework = Coursework(
        class_id=data['class_id'],
        create_time=datetime.datetime.utcnow(),
        deadline=datetime.datetime.fromisoformat(data['deadline']),
        review_set=review_set,
        avg_score=data.get('avg_score', 0.0)
    )
    db.session.add(new_coursework)
    db.session.commit()

    # 添加作业与题库的关联
    for bank_id in data['banks']:
        cw_bank = CwBank(cw_id=new_coursework.cw_id, bank_id=bank_id)
        db.session.add(cw_bank)
    db.session.commit()

    # 如果有互评设置，分配互评任务
    # 如果有互评设置，分配互评任务
    if review_set:
        review_count = int(review_set.split(',')[0].split(':')[1].strip())
        # 获取班级中的所有学生 ID
        student_ids = [sc.student_id for sc in StudentCourses.query.filter_by(class_id=data['class_id']).all()]
        if not student_ids:
            return jsonify({'message': 'No students found in the class'}), 400

        n = len(student_ids)
        if n < 2:
            return jsonify({'message': 'Not enough students to assign peer reviews'}), 400
        if review_count <= 0 or review_count >= n:
            return jsonify({'message': f'Invalid review count: must be between 1 and {n - 1}'}), 400

        # 使用循环分配算法确保均匀分配
        shuffled = random.sample(student_ids, n)
        assignments = []

        # 生成所有评价关系
        for i in range(n):
            reviewer = shuffled[i]
            for j in range(1, review_count + 1):
                reviewee = shuffled[(i + j) % n]
                assignments.append((reviewer, reviewee))

        # 验证分配是否合理
        review_counts = defaultdict(int)
        reviewed_counts = defaultdict(int)

        for reviewer, reviewee in assignments:
            review_counts[reviewer] += 1
            reviewed_counts[reviewee] += 1

        # 检查分配是否均衡
        for sid in student_ids:
            if review_counts[sid] != review_count or reviewed_counts[sid] != review_count:
                return jsonify({'message': 'Failed to create balanced peer review assignments'}), 500

        # 创建互评记录
        for reviewer_id, student_id in assignments:
            matching = Matching(
                reviewer_id=reviewer_id,
                cw_id=new_coursework.cw_id,
                student_id=student_id
            )
            db.session.add(matching)

        db.session.commit()

    return jsonify({'message': 'Coursework created', 'cw_id': new_coursework.cw_id}), 201


@app.route('/api/coursework', methods=['GET'])
def get_coursework():
    class_id = request.args.get('classId')
    coursework_list = Coursework.query.filter_by(class_id=class_id).all()
    result = []
    for cw in coursework_list:
        # 获取关联的题库
        banks = CwBank.query.filter_by(cw_id=cw.cw_id).all()
        bank_ids = [b.bank_id for b in banks]
        bank_details1 = []
        for bank_id in bank_ids:
            bank = db.session.get(Bank, bank_id)
            if bank:
                # 提取 location 的 a 和 b
                location_a, location_b = bank.location.split(':') if bank.location else (None, None)
                bank_details1.append({
                    'bank_id': bank.bank_id,
                    'bank_name': bank.bank_name,
                    'bank_type': bank.bank_type,
                    'location_a': location_a,
                    'location_b': location_b,
                    'display_order': bank.display_order
                })

        # 处理可能为空的 create_time 和 deadline
        create_time = cw.create_time.isoformat() if cw.create_time is not None else None
        deadline = cw.deadline.isoformat() if cw.deadline is not None else None

        result.append({
            'cw_id': cw.cw_id,
            'create_time': create_time,  # 如果为 None，返回 None
            'deadline': deadline,  # 如果为 None，返回 None
            'review_set': cw.review_set,
            'avg_score': cw.avg_score,
            'banks': bank_details1  # 返回完整的题库信息
        })
    return jsonify(result), 200


# 获取题库名称
@app.route('/api/bank/<int:bank_id>', methods=['GET'])
def get_bank(bank_id):
    bank = db.session.get(Bank, bank_id)
    if not bank:
        return jsonify({'message': 'Bank not found'}), 404
    return jsonify({'bank_name': bank.bank_name}), 200


# 获取学生所在的班级
@app.route('/api/student/<int:student_id>/classes', methods=['GET'])
def get_student_classes(student_id):
    classes = db.session.query(Class).join(
        StudentCourses, Class.class_id == StudentCourses.class_id
    ).filter(StudentCourses.student_id == student_id).all()
    class_list = [{'class_id': cls.class_id, 'classname': cls.classname} for cls in classes]
    return jsonify(class_list), 200


# 获取作业的题库信息
@app.route('/api/coursework/<int:cw_id>/banks/<int:student_id>', methods=['GET'])
def get_coursework_banks(cw_id, student_id):
    try:
        coursework = db.session.query(
            Coursework.create_time,
            Coursework.deadline
        ).filter(
            Coursework.cw_id == cw_id
        ).first()

        if not coursework:
            return jsonify({"error": "Coursework not found"}), 404

        create_time = coursework.create_time
        deadline = coursework.deadline
        now = datetime.datetime.now()

        # 2. 查询所有符合条件的银行
        banks = db.session.query(Bank).join(
            CwBank, Bank.bank_id == CwBank.bank_id
        ).filter(
            CwBank.cw_id == cw_id
        ).all()

        # 3. 为每个银行确定状态
        bank_list = []
        for bank in banks:
            # 查询该学生的提交记录
            submission = db.session.query(Submission.sub_time).filter(
                and_(
                    Submission.bank_id == bank.bank_id,
                    Submission.student_id == student_id
                )
            ).order_by(Submission.sub_time.desc()).first()

            # 确定状态值
            if submission:  # 有提交记录
                sub_time = submission.sub_time
                if create_time <= sub_time <= deadline:
                    status = 2
                elif sub_time > deadline:
                    status = 3
                else:
                    status = 0  # 早于create_time的提交(理论上不应该存在)
            else:  # 无提交记录
                if now < create_time:
                    status = 0  # 作业未开始
                elif create_time <= now <= deadline:
                    status = 0  # 可提交状态
                else:
                    status = 1  # 已过期未提交

            bank_list.append({
                'bank_id': bank.bank_id,
                'bank_name': bank.bank_name,
                'bank_type': bank.bank_type,
                'location': bank.location,
                'display_order': bank.display_order,
                'status': status
            })
        return jsonify(bank_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.get_json()
    if not data:
        return jsonify({"error": "无效的提交数据"}), 400

    # 从前端提交数据中分别获取 user、exercise、performance 信息
    user_data = data.get('user', {})
    exercise_data = data.get('exercise', {})
    performance_data = data.get('performance', {})

    # exercise 部分信息
    bank_type = exercise_data.get('bank_type')
    a = exercise_data.get('a')
    b = exercise_data.get('b')
    display_order = exercise_data.get('display_order')
    # 拼接 location，例如 "a:b"
    location = f"{a}:{b}"
    if not (location and bank_type and display_order is not None):
        return jsonify({"error": "缺少必要的 bank 信息"}), 400

    # 根据 bank 的 location、bank_type 和 display_order 查询对应的 bank
    bank = Bank.query.filter_by(location=location, bank_type=bank_type, display_order=display_order).first()
    if not bank:
        return jsonify({"error": "未找到对应的 bank"}), 404
    bank_id = bank.bank_id

    # performance 部分：timer 是以秒为单位，将其转为 hh:mm:ss 格式的 time 对象
    timer_seconds = performance_data.get('timer', 0)
    hours = timer_seconds // 3600
    minutes = (timer_seconds % 3600) // 60
    seconds = timer_seconds % 60
    completion_time = datetime.time(hours, minutes, seconds)

    # student_id 这里暂时使用一个默认值，实际应通过 token 或 session 获取
    student_id = user_data.get('token') or 0

    # 新建 submission 记录
    submission = Submission(
        bank_id=bank_id,
        student_id=student_id,
        sub_time=datetime.datetime.utcnow(),
        score=0,  # 得分稍后计算
        type=bank_type,
        completion_time=completion_time
    )
    db.session.add(submission)
    db.session.flush()  # 生成 submission.sub_id

    total_questions = 0
    correct_count = 0

    # performance.answers 为预处理后的答案数据，格式类似：
    # {
    #   "judgement": { "1": "Y", "2": "N", ... },
    #   "multiChoice": { "20": "BC", "21": "BC", ... },
    #   ... 其他题型
    # }
    answers_data = performance_data.get('answers', {})

    for answer_type, answer_dict in answers_data.items():
        if answer_type == 'multiChoice':
            # 对于 multiChoice 题型，每两个小题为一组
            answer_pairs = []
            for i, (q_number_str, user_ans) in enumerate(answer_dict.items()):
                try:
                    q_number = int(q_number_str)
                except ValueError:
                    continue

                # 获取小题信息
                small_question = (
                    db.session.query(SmallQuestion)
                    .join(BigQuestion, BigQuestion.big_id == SmallQuestion.big_id)
                    .filter(BigQuestion.bank_id == bank_id, SmallQuestion.question_number == q_number)
                    .first()
                )
                if not small_question:
                    continue

                # 将答案保存到 answer_pairs 中
                answer_pairs.append((small_question, user_ans))

                # 每两个小题为一组处理
                if (i + 1) % 2 == 0:
                    if len(answer_pairs) == 2:  # 确保有两个小题
                        total_questions += 2
                        q1, ans1 = answer_pairs[0]
                        q2, ans2 = answer_pairs[1]

                        correct_answer = (q1.question_answer or "").strip()
                        user_answer = str(ans1).strip()

                        if len(user_answer) == 1:
                            user_letters_1 = user_answer[0]
                            user_letters_2 = None
                        elif len(user_answer) == 2:
                            user_letters_1 = user_answer[0]
                            user_letters_2 = user_answer[1]
                        else:
                            user_letters_1 = None
                            user_letters_2 = None
                        # 提取字母进行比较
                        correct_letters_1 = correct_answer[0]
                        correct_letters_2 = correct_answer[1]

                        # 如果用户的答案为空，设置 if_correct 为 None
                        if not user_letters_1 and not user_letters_2:
                            answer = Answer(
                                sub_id=submission.sub_id,
                                question_id=q1.small_id,
                                user_answer=None,
                                if_correct=None
                            )
                            db.session.add(answer)

                            answer = Answer(
                                sub_id=submission.sub_id,
                                question_id=q2.small_id,
                                user_answer=None,
                                if_correct=None
                            )
                            db.session.add(answer)

                        else:
                            # 如果用户有一个字母与标准答案匹配，第一个小题对，第二个小题 if_correct 为 None
                            if user_letters_1 and user_letters_2:
                                if correct_letters_1 == user_letters_1 and correct_letters_2 == user_letters_2:
                                    correct_count += 2  # 两个小题都正确
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q1.small_id,
                                        user_answer=user_answer,
                                        if_correct=user_letters_1 == correct_letters_1
                                    )
                                    db.session.add(answer)
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q2.small_id,
                                        user_answer=user_answer,
                                        if_correct=user_letters_2 == correct_letters_2
                                    )
                                    db.session.add(answer)
                                elif (correct_letters_1 == user_letters_1 and correct_letters_2 != user_letters_2 or
                                      correct_letters_2 == user_letters_1 or correct_letters_1 == user_letters_2 or
                                      correct_letters_2 == user_letters_2 and correct_letters_1 != user_letters_1):
                                    # 第二个小题 if_correct 为 None
                                    correct_count += 1
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q1.small_id,
                                        user_answer=user_answer,
                                        if_correct=True
                                    )
                                    db.session.add(answer)

                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q2.small_id,
                                        user_answer=user_answer,
                                        if_correct=False
                                    )
                                    db.session.add(answer)
                                else:
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q1.small_id,
                                        user_answer=user_answer,
                                        if_correct=False
                                    )
                                    db.session.add(answer)

                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q2.small_id,
                                        user_answer=user_answer,
                                        if_correct=False
                                    )
                                    db.session.add(answer)
                            elif user_letters_1 and not user_letters_2:
                                # 第一小题正确，第二小题 if_correct 为 None
                                if user_letters_1 == correct_letters_1 or user_letters_1 == correct_letters_2:
                                    correct_count += 1
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q1.small_id,
                                        user_answer=user_answer,
                                        if_correct=True
                                    )
                                    db.session.add(answer)

                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q2.small_id,
                                        user_answer=user_answer,
                                        if_correct=None
                                    )
                                    db.session.add(answer)
                                else:
                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q1.small_id,
                                        user_answer=user_answer,
                                        if_correct=False
                                    )
                                    db.session.add(answer)

                                    answer = Answer(
                                        sub_id=submission.sub_id,
                                        question_id=q2.small_id,
                                        user_answer=user_answer,
                                        if_correct=None
                                    )
                                    db.session.add(answer)
                        answer_pairs.clear()  # 清空本次对的答案对
                    continue
            continue
        elif answer_type == 'write':
            for q_number_str, user_ans in answer_dict.items():
                try:
                    q_number = int(q_number_str)
                except ValueError:
                    continue

                # 获取小题信息
                small_question = (
                    db.session.query(SmallQuestion)
                    .join(BigQuestion, BigQuestion.big_id == SmallQuestion.big_id)
                    .filter(BigQuestion.bank_id == bank_id, SmallQuestion.question_number == q_number)
                    .first()
                )
                if not small_question:
                    continue
                submitted_answer = str(user_ans).strip()
                answer = Answer(
                    sub_id=submission.sub_id,
                    question_id=small_question.small_id,
                    user_answer=submitted_answer,
                    if_correct=None
                )
                db.session.add(answer)
                db.session.commit()
                existing_task = task_manager.get_task(submission.sub_id)
                if existing_task and existing_task['status'] == 'processing':
                    return jsonify({"error": "任务已在处理中"}), 400

                task_manager.add_task(submission.sub_id)
                Thread(target=async_evaluate, args=(
                    bank,
                    submission.sub_id,
                    submitted_answer,
                    student_id
                )).start()

                return jsonify({"sub_id": submission.sub_id})
        # 其他题型处理
        for q_number_str, user_ans in answer_dict.items():
            try:
                q_number = int(q_number_str)
            except ValueError:
                continue

            # 获取小题信息
            small_question = (
                db.session.query(SmallQuestion)
                .join(BigQuestion, BigQuestion.big_id == SmallQuestion.big_id)
                .filter(BigQuestion.bank_id == bank_id, SmallQuestion.question_number == q_number)
                .first()
            )
            if not small_question:
                continue

            # 对比答案：简单去除首尾空格后直接比较
            correct_answer = (small_question.question_answer or "").strip()
            submitted_answer = str(user_ans).strip()

            if not submitted_answer:
                if_correct = None
            else:
                if_correct = submitted_answer in correct_answer.split("|")

            if if_correct:
                correct_count += 1
            total_questions += 1

            answer = Answer(
                sub_id=submission.sub_id,
                question_id=small_question.small_id,
                user_answer=submitted_answer,
                if_correct=if_correct
            )
            db.session.add(answer)

    # 计算得分（例如：正确率百分制）
    if total_questions > 0:
        submission.score = (correct_count / total_questions) * 100
    else:
        submission.score = 0

    db.session.commit()

    return jsonify({
        "sub_id": submission.sub_id,
        "score": submission.score
    })


def round_to_nearest_half(number):
    """
    将分数四舍五入到最近的0.5
    规则: 满0.25往上进到上一个数，比如5.25就是5.5，5.24就是5
    """
    multiplied = number * 2
    decimal = multiplied - int(multiplied)

    if decimal >= 0.5:  # 0.25*2=0.5
        rounded = math.ceil(multiplied)
    else:
        rounded = math.floor(multiplied)

    return rounded / 2


def async_evaluate(bank, sub_id, submitted_answer, student_id):
    with app.app_context():
        try:
            task_type = bank.display_order
            title = db.session.query(Resource.resource_information).filter(
                Resource.bank_id == bank.bank_id,
                Resource.resource_type == 'TEXT'
            ).first()
            chart_data = db.session.query(Resource.resource_information).filter(
                Resource.bank_id == bank.bank_id,
                Resource.resource_type == 'describe'
            ).first()
            messages = [
                build_system_message(task_type),
                {
                    "role": "user",
                    "content": build_user_prompt(submitted_answer, title, chart_data)
                }
            ]
            response = client.chat.completions.create(
                model="deepseek-reasoner",
                messages=messages,
                temperature=0.3,
                top_p=0.7,
                stream=False
            )
            # 解析响应
            response_text = response.choices[0].message.content
            parsed = parse_response(response_text)

            # 分数验证
            for score in parsed["scores"].values():
                if not 1 <= score <= 9:
                    raise ValueError("Invalid score range")
            new_review = PeerReview(
                reviewer_id=0,
                reviewer_type="ai",
                student_id=student_id,
                review_time=datetime.datetime.now(),  # 当前时间
                review_information=parsed["evaluation"],
                review_result=json.dumps(parsed["scores"]),
                sub_id=sub_id,
                is_anonymous=False
            )

            # 添加到数据库
            db.session.add(new_review)
            score_values = [float(v) for v in parsed["scores"].values()
                            if isinstance(v, (int, float))]

            if not score_values:
                return None, 'No valid scores provided'

            # 计算平均分并四舍五入
            average = sum(score_values) / len(score_values)
            rounded_score = round_to_nearest_half(average)

            # 更新数据库
            submission = Submission.query.filter_by(sub_id=sub_id).first()
            if not submission:
                return None, 'Submission not found'
            # 更新分数
            submission.score = rounded_score
            db.session.commit()
            task_manager.mark_done(sub_id, parsed["scores"])
        except Exception as e:
            task_manager.mark_done(sub_id, {"error": str(e)})
            return jsonify({
                "error": str(e),
                "advice": "请检查：1.输入格式 2.网络连接 3.API密钥"
            }), 500


@app.route('/api/submission/<int:sub_id>', methods=['GET'])
def get_submission(sub_id):
    async_task = task_manager.get_task(sub_id)
    if async_task:
        # 存在异步任务，需要等待
        if async_task['status'] == 'processing':
            is_done = async_task['event'].wait(timeout=30)
            if not is_done:
                # 返回202和提示信息
                return jsonify({
                    "status": "processing",
                    "message": "任务仍在处理中，请稍后重试",
                    "retry_after": 5  # 可选：提示前端重试间隔
                }), 202
    # 获取对应的 Submission 记录
    submission = Submission.query.filter_by(sub_id=sub_id).first()
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # 获取对应的 Bank 信息
    bank = Bank.query.filter_by(bank_id=submission.bank_id).first()
    if not bank:
        return jsonify({"error": "Bank information not found"}), 404

    if bank.bank_type == "writing":
        latest_ai_review = db.session.query(PeerReview) \
            .filter(
            PeerReview.sub_id == sub_id,
            PeerReview.reviewer_type == "ai",
            PeerReview.reviewer_id == 0
        ) \
            .order_by(PeerReview.review_time.desc()) \
            .first()
        answer = db.session.query(Answer).filter(
            Answer.sub_id == sub_id
        ).first()
        return jsonify({
            "submission_time": submission.sub_time.strftime('%Y-%m-%d %H:%M:%S'),
            "completion_time": submission.completion_time.strftime('%H:%M:%S'),
            "bank_info": {
                "bank_type": bank.bank_type,
                "location": bank.location,
                "display_order": bank.display_order,
                "bank_name": bank.bank_name
            },
            "performance_summary": {
                "result": json.loads(
                    latest_ai_review.review_result) if latest_ai_review and latest_ai_review.review_result else {},
                "information": latest_ai_review.review_information if latest_ai_review else ""
            },
            "answer_details": answer.user_answer
        })
    # 获取成绩统计数据
    total_questions = 0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    answer_details = {}

    # 通过 join 查询答案以及对应的小题（SmallQuestion）
    answers = db.session.query(Answer, SmallQuestion).join(SmallQuestion,
                                                           SmallQuestion.small_id == Answer.question_id).filter(
        Answer.sub_id == sub_id).all()

    for answer, small_question in answers:
        total_questions += 1
        correct_answer = small_question.question_answer.strip() if small_question.question_answer else ""
        user_answer = answer.user_answer.strip() if answer.user_answer else ""
        ic = answer.if_correct
        if ic is True:
            correct_count += 1
            answer_details[small_question.question_number] = {
                'userAnswer': user_answer,
                'correctAnswer': correct_answer,
                'isCorrect': True
            }
        elif ic is False:
            incorrect_count += 1
            answer_details[small_question.question_number] = {
                'userAnswer': user_answer,
                'correctAnswer': correct_answer,
                'isCorrect': False
            }
        else:
            unanswered_count += 1
            answer_details[small_question.question_number] = {
                'userAnswer': None,
                'correctAnswer': correct_answer,
                'isCorrect': False
            }

    accuracy = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    # 返回响应数据
    return jsonify({
        "submission_time": submission.sub_time.strftime('%Y-%m-%d %H:%M:%S'),
        "completion_time": submission.completion_time.strftime('%H:%M:%S'),
        "bank_info": {
            "bank_type": bank.bank_type,
            "location": bank.location,
            "display_order": bank.display_order,
            "bank_name": bank.bank_name
        },
        "performance_summary": {
            "total": total_questions,
            "correct": correct_count,
            "incorrect": incorrect_count,
            "unanswered": unanswered_count,
            "accuracy": accuracy
        },
        "answer_details": answer_details
    })


# 待评价文章接口
@app.route('/api/to-review')
def get_pending_reviews():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({'error': 'Missing student_id'}), 400

    try:
        # 第一步：获取所有匹配记录
        matchings = Matching.query.filter_by(reviewer_id=student_id).all()

        results = []
        for match in matchings:
            # 第二步：获取该cw_id对应的所有bank关联
            cw_banks = CwBank.query.filter_by(cw_id=match.cw_id).all()

            for cw_bank in cw_banks:
                # 第三步：获取bank详细信息
                bank = Bank.query.filter_by(
                    bank_id=cw_bank.bank_id,
                    bank_type='writing'
                ).first()

                if not bank:
                    continue

                # 第四步：获取被评人的最新提交
                submission = Submission.query.filter_by(
                    student_id=match.student_id,
                    bank_id=cw_bank.bank_id
                ).order_by(Submission.sub_time.desc()).first()

                if not submission:
                    continue
                    # 检查是否已经存在peer review记录
                existing_review = PeerReview.query.filter_by(
                    sub_id=submission.sub_id,
                    reviewer_id=student_id,
                    reviewer_type='student'
                ).first()

                if existing_review:
                    continue  # 如果已存在，跳过这条记录
                # 第五步：获取学生信息
                student = db.session.get(Student, match.student_id)

                # 第六步：获取对应的coursework信息（获取review_set）
                coursework = db.session.get(Coursework, match.cw_id)
                class_info = db.session.get(Class, coursework.class_id)
                results.append({
                    'sub_id': submission.sub_id,
                    'student_name': student.username if student else 'Unknown',
                    'review_set': coursework.review_set if coursework else 'Default',
                    'bank_name': bank.bank_name,
                    'location': bank.location,
                    'sub_time': format_datetime(submission.sub_time),
                    'class_name': class_info.classname,
                    'bank_id': cw_bank.bank_id,
                    'display_order': bank.display_order
                })

        return jsonify(results)

    except Exception as e:
        print(f"Error in get_pending_reviews: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


# 收到的评价接口
@app.route('/api/received-reviews')
def get_received_reviews():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({'error': 'Missing student_id'}), 400

    try:
        subquery = db.session.query(
            PeerReview.sub_id,
            func.max(PeerReview.review_time).label('max_review_time')
        ).filter(
            PeerReview.student_id == student_id
        ).group_by(
            PeerReview.sub_id
        ).subquery()

        reviews = db.session.query(PeerReview).join(
            subquery,
            db.and_(
                PeerReview.sub_id == subquery.c.sub_id,
                PeerReview.review_time == subquery.c.max_review_time
            )
        ).all()

        results = []
        for review in reviews:
            # 获取对应的提交信息
            submission = db.session.get(Submission, review.sub_id)
            if not submission:
                continue

            # 获取bank信息
            bank = db.session.get(Bank, submission.bank_id)
            if not bank:
                continue

            # 获取评价人信息
            reviewer_name = 'Anonymous'
            if not review.is_anonymous:
                if review.reviewer_type == 'student':
                    reviewer = db.session.get(Student, review.reviewer_id)
                    reviewer_name = reviewer.username if reviewer else 'Unknown'
                elif review.reviewer_type == 'teacher':
                    reviewer = db.session.get(Teacher, review.reviewer_id)
                    reviewer_name = reviewer.username if reviewer else 'Unknown'
                else:
                    # 当reviewer_type既不是student也不是teacher时，设置为AI
                    reviewer_name = 'AI'

            results.append({
                'sub_id': submission.sub_id,
                'peer_id': review.peer_id,
                'bank_name': bank.bank_name,
                'location': bank.location,
                'display_order': bank.display_order,
                'reviewer_name': reviewer_name,
                'review_time': format_datetime(review.review_time)
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 已做出的评价接口
@app.route('/api/my-reviews')
def get_my_reviews():
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({'error': 'Missing student_id'}), 400

    try:
        # 获取每个sub_id对应的最新评价
        subquery = db.session.query(
            PeerReview.sub_id,
            func.max(PeerReview.review_time).label('max_review_time')
        ).filter(
            PeerReview.reviewer_id == student_id,
            PeerReview.reviewer_type == 'student'
        ).group_by(
            PeerReview.sub_id
        ).subquery()

        # 获取完整的最新评价记录
        reviews = db.session.query(PeerReview).join(
            subquery,
            db.and_(
                PeerReview.sub_id == subquery.c.sub_id,
                PeerReview.review_time == subquery.c.max_review_time
            )
        ).filter(
            PeerReview.reviewer_id == student_id,
            PeerReview.reviewer_type == 'student'
        ).all()

        results = []
        for review in reviews:
            # 获取对应的提交信息
            submission = db.session.get(Submission, review.sub_id)
            if not submission:
                continue

            # 获取bank信息
            bank = db.session.get(Bank, submission.bank_id)
            if not bank:
                continue

            # 获取被评人信息
            reviewee = db.session.get(Student, submission.student_id)

            results.append({
                'peer_id': review.peer_id,
                'bank_name': bank.bank_name,
                'location': bank.location,
                'display_order': bank.display_order,
                'reviewee_name': reviewee.username if reviewee else 'Unknown',
                'review_time': format_datetime(review.review_time),
                'review_result': review.review_result,
                'review_information': review.review_information,
                'sub_id': review.sub_id  # 添加sub_id方便前端使用
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/review/<int:sub_id>')
def get_review_data(sub_id):
    """处理评审页面数据请求
    1. 通过sub_id获取用户答案
    2. 通过sub_id找到bank_id
    3. 通过bank_id获取资源数据"""
    try:
        # 获取用户答案
        answer = Answer.query.filter_by(sub_id=sub_id).first()
        if not answer:
            return jsonify({"error": "Submission not found"}), 404

        # 获取关联的bank_id
        submission = db.session.get(Submission, sub_id)
        if not submission:
            return jsonify({"error": "Bank data not found"}), 404
        bank = db.session.get(Bank, submission.bank_id)
        # 获取资源数据
        text_resource = Resource.query.filter_by(
            bank_id=submission.bank_id,
            resource_type='TEXT'
        ).first()

        picture_resources = Resource.query.filter_by(
            bank_id=submission.bank_id,
            resource_type='picture'
        ).all()

        return jsonify({
            "bank_order": bank.display_order,
            "user_answer": answer.user_answer,
            "student_id": submission.student_id,
            "text": text_resource.resource_information if text_resource else None,
            "pictures": [r.resource_information for r in picture_resources]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/review-details/<int:sub_id>')
def get_review_details(sub_id):
    # 获取请求参数
    reviewer_id = request.args.get('reviewer_id', type=int)
    reviewer_type = request.args.get('reviewer_type')

    # 基础查询
    subquery = db.session.query(
        PeerReview.reviewer_type,
        PeerReview.reviewer_id,
        db.func.max(PeerReview.review_time).label('max_ts')
    ).filter_by(sub_id=sub_id)

    # 检查是否有符合条件的记录
    exists = db.session.query(
        subquery.filter(
            PeerReview.reviewer_id == reviewer_id,
            PeerReview.reviewer_type == reviewer_type
        ).exists()
    ).scalar()
    if exists and reviewer_type != 'teacher':
        subquery = subquery.filter(
            PeerReview.reviewer_id == reviewer_id,
            PeerReview.reviewer_type == reviewer_type
        )

    subquery = subquery.group_by(
        PeerReview.reviewer_type,
        PeerReview.reviewer_id
    ).subquery()

    reviews = PeerReview.query.join(
        subquery,
        (PeerReview.reviewer_type == subquery.c.reviewer_type) &
        (PeerReview.reviewer_id == subquery.c.reviewer_id) &
        (PeerReview.review_time == subquery.c.max_ts)
    ).all()
    result = []
    for review in reviews:
        # 获取用户名
        if review.reviewer_type == 'student':
            user = Student.query.get(review.reviewer_id)
            username = user.username if user else 'Unknown'
        elif review.reviewer_type == 'teacher':
            user = Teacher.query.get(review.reviewer_id)
            username = user.username if user else 'Unknown'
        else:
            username = 'AI'

        # 获取检测结果
        detection = DetectionResults.query.filter_by(
            peer_id=review.peer_id
        ).order_by(DetectionResults.created_at.desc()).first()

        result.append({
            "reviewer_type": review.reviewer_type,
            "reviewer_id": review.reviewer_id,
            "reviewer_name": username,
            "review_info": review.review_information,
            "review_result": review.review_result,
            "detection": {
                "is_fake": detection.is_fake if detection else None,
                "confidence": detection.confidence if detection else None,
                "evaluation": detection.evaluation if detection else None
            } if detection else None
        })
    return jsonify(result)


@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    """处理评分提交请求"""
    data = request.json
    # 这里可以添加数据库存储逻辑
    new_review = PeerReview(
        reviewer_id=data['reviewer_id'],
        reviewer_type=data['reviewer_role'],
        student_id=data['reviewee_id'],
        review_time=datetime.datetime.now(),
        review_information=data['comments'],
        review_result=json.dumps(data['scores']),
        sub_id=data['sub_id'],
        is_anonymous=False
    )
    # 添加到数据库
    db.session.add(new_review)
    db.session.commit()
    try:
        # 假设你的模型类名为 PeerReview
        latest_review = PeerReview.query.filter_by(
            sub_id=data['sub_id'],
            reviewer_type='ai'
        ).order_by(PeerReview.peer_id.desc()).first()

        messages = [
            {
                "role": "system",
                "content": """You are an academic evaluation auditor. Your task is to detect if USER REVIEWS are 
                fake/misleading by comparing with AI's reference evaluation. Follow these steps:

        1. Compare score discrepancies in all dimensions:
           - Significant deviations (e.g., user=9 vs AI=5)
           - Illogical combinations (high score with negative comments)

        2. Analyze comment authenticity:
           - Generic/vague language (e.g., "great work")
           - Contradictions with scores
           - Lack of specific examples

        3. Final judgment must be based on:
           - AI evaluation is the ground truth
           - User review is suspicious if it significantly deviates from AI's assessment

        Return JSON format:
        {
            "is_fake": boolean,
            "confidence": 0-100,
            "evaluation": "Key discrepancy found: [specific reason]"
        }"""
            },
            {
                "role": "user",
                "content": f"""Article Content:
        {data['texts']}

        [AI Reference Evaluation]
        Scores: {latest_review.review_result}
        Comments: {latest_review.review_information}

        [User Evaluation Under Scrutiny]
        Scores: {json.dumps(data['scores'])}
        Comments: {data['comments']}"""
            }
        ]

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.2,  # 更低随机性保证分析严谨性
            top_p=0.3,  # 聚焦最相关特征
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        # 3. Save to database - 保存到数据库
        record = DetectionResults(
            is_fake=result['is_fake'],
            confidence=result['confidence'],
            evaluation=result['evaluation'],
            peer_id=new_review.peer_id
        )
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "success"})


# -----------------------------
# 辅助函数：根据 location 字符串解析排序规则
# -----------------------------
def sort_key(bank):
    # location 格式 "X:Y" —— X 数字越大排前，Y 数字越小排前，最后再按 display_order 升序
    parts = bank.location.split(':') if bank.location and ':' in bank.location else [0, 0]
    try:
        first = int(parts[0])
        second = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        first, second = 0, 0
    return -first, second, bank.display_order if bank.display_order is not None else 0


# -----------------------------
# API 接口实现
# -----------------------------

# 1. 获取所有 Bank（支持模糊搜索、排序，并按 bank_type 分组返回）
@app.route('/api/banks', methods=['GET'])
def get_banks():
    search_query = request.args.get('search', '').strip().lower()
    banks = Bank.query.all()

    if search_query:
        def match(bank1):
            return (search_query in (bank1.bank_name or "").lower() or
                    search_query in (bank1.bank_type or "").lower() or
                    search_query in (bank1.location or "").lower())

        banks = list(filter(match, banks))

    banks.sort(key=sort_key)
    grouped = {}
    for bank in banks:
        group = bank.bank_type if bank.bank_type else 'Undefined'
        if group not in grouped:
            grouped[group] = []
        grouped[group].append({
            'bank_id': bank.bank_id,
            'bank_name': bank.bank_name,
            'bank_type': bank.bank_type,
            'location': bank.location,
            'display_order': bank.display_order
        })
    return jsonify(grouped)


# 2. 获取指定 bank 的详细信息（显式查询 resource、big question 及 small question）
@app.route('/api/banks/<int:bank_id>', methods=['GET'])
def bank_details(bank_id):
    bank = Bank.query.get(bank_id)
    if not bank:
        return jsonify({'error': 'Bank not found'}), 404

    # 显式查询 resource（仅返回 TEXT 与 PICTURE 类型记录）
    resources_query = Resource.query.filter(
        Resource.bank_id == bank_id,
        Resource.resource_type.in_(['TEXT', 'picture'])
    ).all()
    resources = [{
        'resource_id': r.resource_id,
        'resource_information': r.resource_information,
        'resource_type': r.resource_type
    } for r in resources_query]

    # 显式查询 big question
    big_questions_query = BigQuestion.query.filter_by(bank_id=bank_id).all()
    big_questions_data = []
    for bq in big_questions_query:
        # 显式查询对应 small question
        small_questions_query = SmallQuestion.query.filter_by(big_id=bq.big_id).all()
        small_questions_data = []
        for sq in small_questions_query:
            small_questions_data.append({
                'small_id': sq.small_id,
                'question_number': sq.question_number,
                'question_content': sq.question_content,
                'question_options': sq.question_options,
                'question_answer': sq.question_answer
            })
        big_questions_data.append({
            'big_id': bq.big_id,
            'type': bq.type,
            'question_description': bq.question_description,
            'start_number': bq.start_number,
            'end_number': bq.end_number,
            'if_nb': bq.if_nb,
            'small_questions': small_questions_data
        })

    return jsonify({
        'bank': {
            'bank_id': bank.bank_id,
            'bank_name': bank.bank_name,
            'bank_type': bank.bank_type,
            'location': bank.location,
            'display_order': bank.display_order
        },
        'resources': resources,
        'big_questions': big_questions_data
    })


# 3. CRUD 接口 —— Resource
@app.route('/api/resource', methods=['POST'])
def add_resource():
    data = request.json
    try:
        original_path = data.get('resource_information')
        resource_type = data.get('resource_type')
        filename = os.path.basename(original_path)
        if resource_type == "PICTURE":
            new_path = f'../../../src/assets/{filename}'
        else:
            new_path = original_path
        resource_type = resource_type.lower() if resource_type == "PICTURE" else resource_type
        new_resource = Resource(
            resource_information=new_path,
            resource_type=resource_type,
            bank_id=data.get('bank_id')
        )
        db.session.add(new_resource)
        db.session.commit()
        return jsonify({'message': 'Resource added', 'resource_id': new_resource.resource_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/resource/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    data = request.json
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    try:
        original_path = data.get('resource_information', resource.resource_information)
        # 转换路径
        filename = os.path.basename(original_path)
        resource_type = data.get('resource_type', resource.resource_type)
        if resource_type == "PICTURE":
            new_path = f'../../../src/assets/{filename}'
        else:
            new_path = original_path
        resource.resource_information = new_path
        resource_type = resource_type.lower() if resource_type == "PICTURE" else resource_type
        resource.resource_type = resource_type
        db.session.commit()
        return jsonify({'message': 'Resource updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/resource/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    try:
        # Delete the physical file if it's a picture
        if resource.resource_type.lower() == "picture":
            filename = os.path.basename(resource.resource_information)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as file_error:
                # Log the file deletion error but continue with database deletion
                app.logger.error(f"Failed to delete file {file_path}: {str(file_error)}")
        db.session.delete(resource)
        db.session.commit()
        return jsonify({'message': 'Resource deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 4. CRUD 接口 —— BigQuestion
@app.route('/api/bigquestion', methods=['POST'])
def add_bigquestion():
    data = request.json
    try:
        new_bq = BigQuestion(
            bank_id=data.get('bank_id'),
            type=data.get('type'),
            question_description=data.get('question_description'),
            start_number=data.get('start_number'),
            end_number=data.get('end_number'),
            if_nb=data.get('if_nb')
        )
        db.session.add(new_bq)
        db.session.commit()
        return jsonify({'message': 'BigQuestion added', 'big_id': new_bq.big_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/bigquestion/<int:big_id>', methods=['PUT'])
def update_bigquestion(big_id):
    data = request.json
    bq = BigQuestion.query.get(big_id)
    if not bq:
        return jsonify({'error': 'BigQuestion not found'}), 404
    try:
        bq.type = data.get('type', bq.type)
        bq.question_description = data.get('question_description', bq.question_description)
        bq.start_number = data.get('start_number', bq.start_number)
        bq.end_number = data.get('end_number', bq.end_number)
        bq.if_nb = data.get('if_nb', bq.if_nb)
        db.session.commit()
        return jsonify({'message': 'BigQuestion updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/bigquestion/<int:big_id>', methods=['DELETE'])
def delete_bigquestion(big_id):
    bq = BigQuestion.query.get(big_id)
    if not bq:
        return jsonify({'error': 'BigQuestion not found'}), 404
    try:
        db.session.delete(bq)
        db.session.commit()
        return jsonify({'message': 'BigQuestion deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 5. CRUD 接口 —— SmallQuestion
@app.route('/api/smallquestion', methods=['POST'])
def add_smallquestion():
    data = request.json
    try:
        new_sq = SmallQuestion(
            big_id=data.get('big_id'),
            question_number=data.get('question_number'),
            question_content=data.get('question_content'),
            question_options=data.get('question_options'),
            question_answer=data.get('question_answer')
        )
        db.session.add(new_sq)
        db.session.commit()
        return jsonify({'message': 'SmallQuestion added', 'small_id': new_sq.small_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/smallquestion/<int:small_id>', methods=['PUT'])
def update_smallquestion(small_id):
    data = request.json
    sq = SmallQuestion.query.get(small_id)
    if not sq:
        return jsonify({'error': 'SmallQuestion not found'}), 404
    try:
        sq.question_number = data.get('question_number', sq.question_number)
        sq.question_content = data.get('question_content', sq.question_content)
        sq.question_options = data.get('question_options', sq.question_options)
        sq.question_answer = data.get('question_answer', sq.question_answer)
        db.session.commit()
        return jsonify({'message': 'SmallQuestion updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/smallquestion/<int:small_id>', methods=['DELETE'])
def delete_smallquestion(small_id):
    sq = SmallQuestion.query.get(small_id)
    if not sq:
        return jsonify({'error': 'SmallQuestion not found'}), 404
    try:
        db.session.delete(sq)
        db.session.commit()
        return jsonify({'message': 'SmallQuestion deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 1. /api/upload 文件上传接口
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    # 保存到指定目录，这里你可以改为保存到 vue 项目中的 src/assets
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    return jsonify({'filePath': f'/vue-project/src/assets/{filename}'})


# 2. 添加 Bank 接口（POST /api/bank）
@app.route('/api/bank', methods=['POST'])
def add_bank():
    data = request.json
    try:
        new_bank = Bank(
            bank_name=data.get('bank_name'),
            bank_type=data.get('bank_type'),
            location=data.get('location'),
            display_order=data.get('display_order')
        )
        db.session.add(new_bank)
        db.session.commit()
        return jsonify({'message': 'Bank added', 'bank_id': new_bank.bank_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 3. 修改 Bank 接口（PUT /api/bank/<int:bank_id>）
@app.route('/api/bank/<int:bank_id>', methods=['PUT'])
def update_bank(bank_id):
    data = request.json
    bank = Bank.query.get(bank_id)
    if not bank:
        return jsonify({'error': 'Bank not found'}), 404
    try:
        bank.bank_name = data.get('bank_name', bank.bank_name)
        bank.bank_type = data.get('bank_type', bank.bank_type)
        bank.location = data.get('location', bank.location)
        bank.display_order = data.get('display_order', bank.display_order)
        db.session.commit()
        return jsonify({'message': 'Bank updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# 4. 删除 Bank 接口（DELETE /api/bank/<int:bank_id>）
@app.route('/api/bank/<int:bank_id>', methods=['DELETE'])
def delete_bank(bank_id):
    bank = Bank.query.get(bank_id)
    if not bank:
        return jsonify({'error': 'Bank not found'}), 404
    try:
        db.session.delete(bank)
        db.session.commit()
        return jsonify({'message': 'Bank deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


def get_student_submissions_logic(student_id, class_id):
    """核心提交查询逻辑（被多个接口复用）"""
    # 获取班级所有coursework和bank的映射
    cw_banks = db.session.query(
        CwBank.cw_id,
        CwBank.bank_id,
        Coursework.create_time,
        Coursework.deadline
    ).join(Coursework, CwBank.cw_id == Coursework.cw_id
           ).filter(Coursework.class_id == class_id).all()

    results = []
    for cw in cw_banks:
        # 分两步查询：先查按时提交，再查逾期提交
        valid_sub = db.session.query(Submission).filter(
            Submission.student_id == student_id,
            Submission.bank_id == cw.bank_id,
            Submission.sub_time >= cw.create_time,
            Submission.sub_time <= cw.deadline
        ).order_by(Submission.sub_time.desc()).first()

        late_sub = db.session.query(Submission).filter(
            Submission.student_id == student_id,
            Submission.bank_id == cw.bank_id,
            Submission.sub_time > cw.deadline
        ).order_by(Submission.sub_time.desc()).first()

        final_sub = valid_sub or late_sub
        bank_info = Bank.query.get(cw.bank_id)

        results.append({
            "cw_id": cw.cw_id,
            "bank_id": cw.bank_id,
            "sub_id": final_sub.sub_id if final_sub else "None",
            "bank_name": bank_info.bank_name,
            "bank_type": bank_info.bank_type,
            "status": "Submitted" if final_sub else "Unsubmitted",
            "sub_time": final_sub.sub_time.isoformat() if final_sub else None,
            "score": final_sub.score if final_sub else None,
            "is_late": final_sub.sub_time > cw.deadline if final_sub else False
        })
    return results


def _calculate_average(scores):
    """独立计算平均分函数"""
    if not scores:  # 空列表或None
        return None
    return round(sum(scores) / len(scores), 2)


# 后端 app.py 完整补充
@app.route('/api/check/<int:class_id>')
def get_class_data(class_id):
    """班级概览接口（使用提交逻辑统一计算）"""
    try:
        # 获取班级学生基础信息
        students = db.session.query(
            Student.student_id,
            Student.username
        ).join(StudentCourses, Student.student_id == StudentCourses.student_id
               ).filter(StudentCourses.class_id == class_id).all()

        # 获取课程作业结构
        courseworks = db.session.query(
            Coursework.cw_id,
            Coursework.create_time,
            Coursework.deadline
        ).filter(Coursework.class_id == class_id).all()

        # 获取所有bank映射
        cw_banks = db.session.query(
            CwBank.cw_id,
            CwBank.bank_id,
            Bank.bank_name,
            Bank.bank_type
        ).join(Bank, CwBank.bank_id == Bank.bank_id
               ).filter(CwBank.cw_id.in_([cw.cw_id for cw in courseworks])).all()

        # 为所有学生计算平均分
        student_stats = {}
        for student in students:
            submissions = get_student_submissions_logic(student.student_id, class_id)

            # 按类型分组分数（排除未提交）
            scores = {'listening': [], 'reading': [], 'writing': []}
            for sub in submissions:
                if sub['score'] is not None:  # 明确过滤未提交
                    scores[sub['bank_type'].lower()].append(sub['score'])

            # 计算各科平均分
            averages = {
                'listening': _calculate_average(scores['listening']),
                'reading': _calculate_average(scores['reading']),
                'writing': _calculate_average(scores['writing'])
            }
            student_stats[student.student_id] = averages

        return jsonify({
            "students": [{
                "id": s.student_id,
                "name": s.username,
                "averages": student_stats.get(s.student_id, {})
            } for s in students],
            "courseworks": [{
                "cw_id": cw.cw_id,
                "banks": [{
                    "id": cb.bank_id,
                    "name": cb.bank_name,
                    "type": cb.bank_type.lower()
                } for cb in cw_banks if cb.cw_id == cw.cw_id]
            } for cw in courseworks]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/submissions/<int:student_id>')
def get_submissions(student_id):
    """学生提交详情接口"""
    try:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({"error": "Missing class_id parameter"}), 400

        submissions = get_student_submissions_logic(student_id, class_id)
        return jsonify(submissions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reviews/<int:student_id>')
def get_reviews1(student_id):
    """学生互评详情接口（返回包含cw_id和sub_id的完整数据）"""
    try:
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({"error": "Missing class_id parameter"}), 400

        # 1. 获取班级其他学生ID
        other_students = db.session.query(
            StudentCourses.student_id,
            Student.username
        ).join(Student, StudentCourses.student_id == Student.student_id
               ).filter(
            StudentCourses.class_id == class_id,
            StudentCourses.student_id != student_id
        ).all()

        if not other_students:
            return jsonify([])

        # 2. 收集所有有效提交记录（保留cw_id和sub_id的映射）
        submission_map = {}  # {sub_id: {'cw_id': x, 'bank_name': y, 'student_id': z}}
        for other_id, username in other_students:
            submissions = get_student_submissions_logic(other_id, class_id)
            for sub in submissions:
                if sub['sub_id'] != "None":
                    submission_map[int(sub['sub_id'])] = {
                        'cw_id': sub['cw_id'],
                        'bank_name': sub['bank_name'],
                        'bank_type': sub['bank_type'],
                        'target_student': username,
                        'target_student_id': other_id
                    }

        if not submission_map:
            return jsonify([])

        # 3. 查询互评记录
        latest_reviews = db.session.query(
            PeerReview.sub_id,
            func.max(PeerReview.peer_id).label('latest_peer_id')
        ).filter(
            PeerReview.reviewer_id == student_id,
            PeerReview.reviewer_type == 'student',
            PeerReview.sub_id.in_(list(submission_map.keys()))
        ).group_by(PeerReview.sub_id).subquery()

        reviews = db.session.query(
            PeerReview.peer_id,
            PeerReview.review_result,
            PeerReview.sub_id
        ).join(latest_reviews,
               PeerReview.peer_id == latest_reviews.c.latest_peer_id
               ).all()

        # 4. 构建完整响应
        result = []
        for r in reviews:
            sub_info = submission_map[r.sub_id]
            detection = DetectionResults.query.filter_by(peer_id=r.peer_id).first()
            result.append({
                "id": r.peer_id,
                "sub_id": r.sub_id,  # 新增
                "cw_id": sub_info['cw_id'],  # 新增
                "bank_type": sub_info['bank_type'],
                "assignment": sub_info['bank_name'],
                "target_student": sub_info['target_student'],
                "target_student_id": sub_info['target_student_id'],  # 新增
                "result": r.review_result,
                "is_fake": detection.is_fake if detection else None,
                "confidence": detection.confidence if detection else None
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
