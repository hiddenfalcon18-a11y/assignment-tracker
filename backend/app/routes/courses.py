"""
Course management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Course, Language, Group
from app.schemas import CourseCreate, CourseResponse, CourseUpdate, LanguageCreate, LanguageResponse

router = APIRouter(prefix="/api/courses", tags=["courses"])

# ============ Language Management ============

@router.post("/languages", response_model=LanguageResponse, status_code=status.HTTP_201_CREATED)
async def create_language(
    language: LanguageCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new programming language/course category
    Supports: C++, C, Python, ISTQB, Java, JavaScript, etc.
    """
    # Check if language already exists
    existing = db.query(Language).filter(Language.name == language.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language already exists"
        )
    
    db_language = Language(
        name=language.name,
        description=language.description
    )
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

@router.get("/languages", response_model=List[LanguageResponse])
async def get_all_languages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all available languages
    """
    languages = db.query(Language).offset(skip).limit(limit).all()
    return languages

@router.get("/languages/{language_id}", response_model=LanguageResponse)
async def get_language(
    language_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific language
    """
    language = db.query(Language).filter(Language.id == language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    return language

# ============ Course CRUD Operations ============

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new course
    """
    # Verify language exists
    language = db.query(Language).filter(Language.id == course.language_id).first()
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Language not found"
        )
    
    db_course = Course(
        name=course.name,
        description=course.description,
        language_id=course.language_id,
        difficulty_level=course.difficulty_level,
        duration_hours=course.duration_hours
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/", response_model=List[CourseResponse])
async def get_all_courses(
    language_id: int = None,
    difficulty: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all courses with optional filters
    """
    query = db.query(Course)
    
    if language_id:
        query = query.filter(Course.language_id == language_id)
    
    if difficulty:
        query = query.filter(Course.difficulty_level == difficulty)
    
    courses = query.offset(skip).limit(limit).all()
    return courses

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific course
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_update: CourseUpdate,
    db: Session = Depends(get_db)
):
    """
    Update course details
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    update_data = course_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a course (Admin only)
    """
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    db.delete(db_course)
    db.commit()

# ============ Assign Courses to Groups ============

@router.post("/{course_id}/groups/{group_id}", response_model=CourseResponse)
async def assign_course_to_group(
    course_id: int,
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Assign a course to a group
    This is the KEY FEATURE - Admin can assign language courses to employee groups
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if course already assigned to group
    if course in group.courses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course already assigned to this group"
        )
    
    course.groups.append(group)
    db.commit()
    db.refresh(course)
    return course

@router.delete("/{course_id}/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course_from_group(
    course_id: int,
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove a course from a group
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if course not in group.courses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course not assigned to this group"
        )
    
    course.groups.remove(group)
    db.commit()

@router.get("/{course_id}/groups", response_model=List)
async def get_course_groups(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all groups assigned to a course
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course.groups

# ============ Bulk Course Assignment ============

@router.post("/groups/{group_id}/bulk-assign")
async def bulk_assign_courses_to_group(
    group_id: int,
    course_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    Bulk assign multiple courses to a group
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    if len(courses) != len(course_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more courses not found"
        )
    
    assigned_count = 0
    for course in courses:
        if course not in group.courses:
            course.groups.append(group)
            assigned_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully assigned {assigned_count} courses to group",
        "group_id": group_id,
        "assigned_count": assigned_count,
        "courses": [{"id": c.id, "name": c.name} for c in courses]
    }

# ============ Get Group's Courses ============

@router.get("/groups/{group_id}/courses", response_model=List[CourseResponse])
async def get_group_courses(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all courses assigned to a group
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group.courses
