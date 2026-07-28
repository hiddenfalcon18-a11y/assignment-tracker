"""
Assessment and exam management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Assessment, AssessmentType, Question, AssessmentResult, Answer, Employee
from app.schemas import AssessmentCreate, AssessmentResponse, AssessmentUpdate, QuestionCreate, QuestionResponse

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

# ============ Assessment CRUD ============

@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment: AssessmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new assessment for a group
    Types: weekly, monthly, yearly
    """
    db_assessment = Assessment(
        group_id=assessment.group_id,
        course_id=assessment.course_id,
        assessment_type=assessment.assessment_type,
        title=assessment.title,
        description=assessment.description,
        total_questions=assessment.total_questions,
        passing_score=assessment.passing_score,
        duration_minutes=assessment.duration_minutes,
        created_by=1  # Change to current user ID
    )
    
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@router.get("/", response_model=List[AssessmentResponse])
async def get_assessments(
    group_id: int = None,
    assessment_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get assessments with filters
    """
    query = db.query(Assessment)
    
    if group_id:
        query = query.filter(Assessment.group_id == group_id)
    
    if assessment_type:
        query = query.filter(Assessment.assessment_type == assessment_type)
    
    assessments = query.offset(skip).limit(limit).all()
    return assessments

@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific assessment with questions
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    return assessment

@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: int,
    assessment_update: AssessmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Update assessment details
    """
    db_assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not db_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    update_data = assessment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assessment, field, value)
    
    db.commit()
    db.refresh(db_assessment)
    return db_assessment

@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an assessment
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    db.delete(assessment)
    db.commit()

# ============ Question Management ============

@router.post("/{assessment_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def add_question_to_assessment(
    assessment_id: int,
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Add a question to an assessment
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    db_question = Question(
        assessment_id=assessment_id,
        question_text=question.question_text,
        question_type=question.question_type,
        options=question.options,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        difficulty=question.difficulty,
        tags=question.tags,
        generated_by_ai=False
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@router.get("/{assessment_id}/questions", response_model=List[QuestionResponse])
async def get_assessment_questions(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all questions for an assessment
    """
    questions = db.query(Question).filter(Question.assessment_id == assessment_id).all()
    return questions

# ============ Assessment Distribution ============

@router.post("/{assessment_id}/distribute-to-group")
async def distribute_assessment_to_group(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Distribute assessment to all employees in the group
    """
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Get all employees in the group
    employees = db.query(Employee).join(
        Employee.groups
    ).filter(assessment.group_id).all()
    
    # Create assessment result records for each employee
    for employee in employees:
        result = AssessmentResult(
            assessment_id=assessment_id,
            employee_id=employee.id,
            score=0,
            max_score=assessment.total_questions * 100 / assessment.total_questions,
            percentage=0,
            status="pending",
            started_at=datetime.utcnow()
        )
        db.add(result)
    
    db.commit()
    
    return {
        "message": "Assessment distributed successfully",
        "assessment_id": assessment_id,
        "employees_count": len(employees)
    }

# ============ Assessment Results ============

@router.get("/{assessment_id}/results")
async def get_assessment_results(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all results for an assessment
    """
    results = db.query(AssessmentResult).filter(
        AssessmentResult.assessment_id == assessment_id
    ).all()
    return results

@router.get("/employee/{employee_id}/results")
async def get_employee_assessment_results(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all assessment results for an employee
    """
    results = db.query(AssessmentResult).filter(
        AssessmentResult.employee_id == employee_id
    ).all()
    return results

# ============ Weekly/Monthly/Yearly Assessment Helpers ============

@router.post("/generate-weekly-assessment")
async def generate_weekly_assessment(
    group_id: int,
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a weekly assessment for a group
    AI automatically generates 10-15 questions
    """
    from app.config import settings
    
    assessment = Assessment(
        group_id=group_id,
        course_id=course_id,
        assessment_type=AssessmentType.WEEKLY,
        title=f"Weekly Assessment - Week {datetime.now().isocalendar()[1]}",
        description="Weekly assessment generated by AI",
        total_questions=settings.WEEKLY_QUESTIONS_COUNT,
        passing_score=60.0,
        duration_minutes=30,
        created_by=1
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "message": "Weekly assessment created",
        "assessment_id": assessment.id,
        "questions_count": settings.WEEKLY_QUESTIONS_COUNT
    }

@router.post("/generate-monthly-assessment")
async def generate_monthly_assessment(
    group_id: int,
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a monthly assessment for a group
    """
    from app.config import settings
    
    assessment = Assessment(
        group_id=group_id,
        course_id=course_id,
        assessment_type=AssessmentType.MONTHLY,
        title=f"Monthly Assessment - {datetime.now().strftime('%B %Y')}",
        description="Monthly comprehensive assessment",
        total_questions=settings.MONTHLY_QUESTIONS_COUNT,
        passing_score=70.0,
        duration_minutes=120,
        created_by=1
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "message": "Monthly assessment created",
        "assessment_id": assessment.id,
        "questions_count": settings.MONTHLY_QUESTIONS_COUNT
    }

@router.post("/generate-yearly-assessment")
async def generate_yearly_assessment(
    group_id: int,
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Generate a yearly assessment for a group
    """
    from app.config import settings
    
    assessment = Assessment(
        group_id=group_id,
        course_id=course_id,
        assessment_type=AssessmentType.YEARLY,
        title=f"Yearly Assessment - {datetime.now().year}",
        description="Comprehensive yearly certification exam",
        total_questions=settings.YEARLY_QUESTIONS_COUNT,
        passing_score=75.0,
        duration_minutes=180,
        created_by=1
    )
    
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    
    return {
        "message": "Yearly assessment created",
        "assessment_id": assessment.id,
        "questions_count": settings.YEARLY_QUESTIONS_COUNT
    }
