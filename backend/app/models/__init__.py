"""
Database models for the application
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base

# Association tables for many-to-many relationships
group_employees = Table(
    'group_employees',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('employee_id', Integer, ForeignKey('employees.id'), primary_key=True)
)

group_courses = Table(
    'group_courses',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('groups.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)

course_materials = Table(
    'course_materials',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('material_id', Integer, ForeignKey('training_materials.id'), primary_key=True)
)

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class AssessmentType(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
    assessments = relationship("Assessment", back_populates="created_by")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    employee_code = Column(String, unique=True, index=True)
    department = Column(String)
    designation = Column(String)
    skills = Column(Text)  # JSON string of skills
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employee")
    groups = relationship("Group", secondary=group_employees, back_populates="employees")
    assessment_results = relationship("AssessmentResult", back_populates="employee")

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    department = Column(String)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employees = relationship("Employee", secondary=group_employees, back_populates="groups")
    courses = relationship("Course", secondary=group_courses, back_populates="groups")
    assessments = relationship("Assessment", back_populates="group")

class Language(Base):
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # C++, C, Python, ISTQB, etc.
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    courses = relationship("Course", back_populates="language")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    language_id = Column(Integer, ForeignKey('languages.id'))
    difficulty_level = Column(String)  # beginner, intermediate, advanced
    duration_hours = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    language = relationship("Language", back_populates="courses")
    groups = relationship("Group", secondary=group_courses, back_populates="courses")
    materials = relationship("TrainingMaterial", back_populates="course")
    assessments = relationship("Assessment", back_populates="course")

class TrainingMaterial(Base):
    __tablename__ = "training_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'))
    title = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)  # pdf, pptx, txt, docx
    content_extracted = Column(Text)  # Extracted text from file
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    
    # Relationships
    course = relationship("Course", back_populates="materials")

class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    assessment_type = Column(Enum(AssessmentType))  # weekly, monthly, yearly
    title = Column(String, index=True)
    description = Column(Text)
    total_questions = Column(Integer)
    passing_score = Column(Float, default=60.0)
    duration_minutes = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="assessments")
    course = relationship("Course", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by], back_populates="assessments")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    question_text = Column(Text)
    question_type = Column(String)  # multiple_choice, true_false, short_answer, essay
    options = Column(Text)  # JSON string for multiple choice
    correct_answer = Column(Text)
    explanation = Column(Text)
    difficulty = Column(String)  # easy, medium, hard
    tags = Column(Text)  # JSON string of tags
    generated_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey('assessments.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    score = Column(Float)
    max_score = Column(Float)
    percentage = Column(Float)
    status = Column(String)  # passed, failed, pending
    time_taken_minutes = Column(Integer)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    feedback = Column(Text)  # AI-generated feedback
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment = relationship("Assessment", back_populates="results")
    employee = relationship("Employee", back_populates="assessment_results")
    answers = relationship("Answer", back_populates="assessment_result", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_result_id = Column(Integer, ForeignKey('assessment_results.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer_text = Column(Text)
    is_correct = Column(Boolean)
    score_awarded = Column(Float)
    ai_evaluation = Column(Text)  # JSON with AI evaluation details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    assessment_result = relationship("AssessmentResult", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Certification(Base):
    __tablename__ = "certifications"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    assessment_result_id = Column(Integer, ForeignKey('assessment_results.id'))
    certificate_code = Column(String, unique=True, index=True)
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    expiry_date = Column(DateTime(timezone=True))
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
