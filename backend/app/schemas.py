"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============ User Schemas ============
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Group Schemas ============
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    department: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None

class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GroupWithEmployees(GroupResponse):
    employees: List['EmployeeResponse'] = []

class GroupWithCourses(GroupResponse):
    courses: List['CourseResponse'] = []

# ============ Language Schemas ============
class LanguageBase(BaseModel):
    name: str
    description: Optional[str] = None

class LanguageCreate(LanguageBase):
    pass

class LanguageResponse(LanguageBase):
    id: int
    
    class Config:
        from_attributes = True

# ============ Course Schemas ============
class CourseBase(BaseModel):
    name: str
    description: Optional[str] = None
    language_id: int
    difficulty_level: str
    duration_hours: int

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    duration_hours: Optional[int] = None

class CourseResponse(CourseBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============ Employee Schemas ============
class EmployeeBase(BaseModel):
    employee_code: str
    department: str
    designation: str
    skills: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    user_id: int

class EmployeeResponse(EmployeeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EmployeeWithGroups(EmployeeResponse):
    groups: List[GroupResponse] = []

# ============ Training Material Schemas ============
class TrainingMaterialBase(BaseModel):
    title: str
    file_type: str

class TrainingMaterialCreate(TrainingMaterialBase):
    course_id: int

class TrainingMaterialResponse(TrainingMaterialBase):
    id: int
    course_id: int
    file_path: str
    content_extracted: Optional[str] = None
    processed: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# ============ Assessment Schemas ============
class QuestionBase(BaseModel):
    question_text: str
    question_type: str  # multiple_choice, true_false, short_answer, essay
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str

class QuestionCreate(QuestionBase):
    options: Optional[str] = None
    tags: Optional[str] = None

class QuestionResponse(QuestionBase):
    id: int
    options: Optional[str] = None
    tags: Optional[str] = None
    generated_by_ai: bool
    
    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    title: str
    description: Optional[str] = None
    assessment_type: str  # weekly, monthly, yearly
    total_questions: int
    passing_score: float = 60.0
    duration_minutes: int

class AssessmentCreate(AssessmentBase):
    group_id: int
    course_id: int

class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    passing_score: Optional[float] = None
    duration_minutes: Optional[int] = None

class AssessmentResponse(AssessmentBase):
    id: int
    group_id: int
    course_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    questions: List[QuestionResponse] = []
    
    class Config:
        from_attributes = True

# ============ Assessment Result Schemas ============
class AnswerBase(BaseModel):
    answer_text: str

class AnswerResponse(AnswerBase):
    id: int
    question_id: int
    is_correct: bool
    score_awarded: float
    ai_evaluation: Optional[str] = None
    
    class Config:
        from_attributes = True

class AssessmentResultBase(BaseModel):
    score: float
    max_score: float
    status: str  # passed, failed, pending

class AssessmentResultResponse(AssessmentResultBase):
    id: int
    assessment_id: int
    employee_id: int
    percentage: float
    time_taken_minutes: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    answers: List[AnswerResponse] = []
    
    class Config:
        from_attributes = True

# ============ Certification Schemas ============
class CertificationBase(BaseModel):
    certificate_code: str

class CertificationResponse(CertificationBase):
    id: int
    employee_id: int
    course_id: int
    assessment_result_id: int
    issued_date: datetime
    expiry_date: Optional[datetime] = None
    is_valid: bool
    
    class Config:
        from_attributes = True

# ============ Response Schemas ============
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    data: List

# Update forward references
GroupWithEmployees.update_forward_refs()
GroupWithCourses.update_forward_refs()
EmployeeWithGroups.update_forward_refs()
