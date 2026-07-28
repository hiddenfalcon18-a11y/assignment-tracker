"""
Admin dashboard and analytics routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Group, Assessment, AssessmentResult, Employee, User, Course, Language

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ============ Dashboard Statistics ============

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get overall dashboard statistics
    """
    total_groups = db.query(Group).count()
    total_employees = db.query(Employee).count()
    total_courses = db.query(Course).count()
    total_assessments = db.query(Assessment).count()
    total_results = db.query(AssessmentResult).count()
    
    # Average score
    avg_score = db.query(func.avg(AssessmentResult.percentage)).scalar() or 0
    
    # Assessments this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    assessments_week = db.query(AssessmentResult).filter(
        AssessmentResult.completed_at >= week_ago
    ).count()
    
    # Passing rate
    passed = db.query(AssessmentResult).filter(
        AssessmentResult.status == "passed"
    ).count()
    passing_rate = (passed / total_results * 100) if total_results > 0 else 0
    
    return {
        "total_groups": total_groups,
        "total_employees": total_employees,
        "total_courses": total_courses,
        "total_assessments": total_assessments,
        "total_assessment_results": total_results,
        "average_score": round(avg_score, 2),
        "assessments_this_week": assessments_week,
        "passing_rate": round(passing_rate, 2)
    }

# ============ Group Analytics ============

@router.get("/groups/{group_id}/analytics")
async def get_group_analytics(
    group_id: int,
    db: Session = Depends(get_db)
):
    """
    Get analytics for a specific group
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Group statistics
    employee_count = len(group.employees)
    course_count = len(group.courses)
    
    # Assessment statistics
    assessments = db.query(Assessment).filter(
        Assessment.group_id == group_id
    ).all()
    
    # Results for this group
    assessment_ids = [a.id for a in assessments]
    results = db.query(AssessmentResult).filter(
        AssessmentResult.assessment_id.in_(assessment_ids)
    ).all() if assessment_ids else []
    
    if results:
        avg_score = sum(r.percentage for r in results) / len(results)
        passed = sum(1 for r in results if r.status == "passed")
        passing_rate = (passed / len(results)) * 100
    else:
        avg_score = 0
        passing_rate = 0
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "employee_count": employee_count,
        "course_count": course_count,
        "total_assessments": len(assessments),
        "total_results": len(results),
        "average_score": round(avg_score, 2),
        "passing_rate": round(passing_rate, 2),
        "assessment_types": {
            "weekly": len([a for a in assessments if a.assessment_type == "weekly"]),
            "monthly": len([a for a in assessments if a.assessment_type == "monthly"]),
            "yearly": len([a for a in assessments if a.assessment_type == "yearly"])
        }
    }

# ============ Course Analytics ============

@router.get("/courses/{course_id}/analytics")
async def get_course_analytics(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Get analytics for a specific course
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Course statistics
    group_count = len(course.groups)
    
    # Get all assessments for this course
    assessments = db.query(Assessment).filter(
        Assessment.course_id == course_id
    ).all()
    
    # Get results
    assessment_ids = [a.id for a in assessments]
    results = db.query(AssessmentResult).filter(
        AssessmentResult.assessment_id.in_(assessment_ids)
    ).all() if assessment_ids else []
    
    if results:
        avg_score = sum(r.percentage for r in results) / len(results)
        passed = sum(1 for r in results if r.status == "passed")
        passing_rate = (passed / len(results)) * 100
    else:
        avg_score = 0
        passing_rate = 0
    
    return {
        "course_id": course_id,
        "course_name": course.name,
        "language": course.language.name if course.language else "N/A",
        "difficulty": course.difficulty_level,
        "groups_assigned": group_count,
        "total_assessments": len(assessments),
        "total_attempts": len(results),
        "average_score": round(avg_score, 2),
        "passing_rate": round(passing_rate, 2)
    }

# ============ Employee Progress ============

@router.get("/employees/{employee_id}/progress")
async def get_employee_progress(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed progress for an employee
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Get all results
    results = db.query(AssessmentResult).filter(
        AssessmentResult.employee_id == employee_id
    ).all()
    
    if results:
        avg_score = sum(r.percentage for r in results) / len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
    else:
        avg_score = 0
        passed = 0
        failed = 0
    
    # Get group assignments
    groups = employee.groups
    
    # Assessment type breakdown
    weekly_results = [r for r in results if "weekly" in r.assessment.assessment_type.lower()]
    monthly_results = [r for r in results if "monthly" in r.assessment.assessment_type.lower()]
    yearly_results = [r for r in results if "yearly" in r.assessment.assessment_type.lower()]
    
    return {
        "employee_id": employee_id,
        "employee_code": employee.employee_code,
        "full_name": employee.user.full_name if employee.user else "N/A",
        "department": employee.department,
        "designation": employee.designation,
        "groups": [{"id": g.id, "name": g.name} for g in groups],
        "total_assessments": len(results),
        "passed": passed,
        "failed": failed,
        "average_score": round(avg_score, 2),
        "assessment_breakdown": {
            "weekly": len(weekly_results),
            "monthly": len(monthly_results),
            "yearly": len(yearly_results)
        },
        "recent_results": [
            {
                "assessment_id": r.assessment_id,
                "assessment_title": r.assessment.title,
                "score": r.percentage,
                "status": r.status,
                "completed_at": r.completed_at
            }
            for r in sorted(results, key=lambda x: x.completed_at or datetime.min, reverse=True)[:5]
        ]
    }

# ============ Language Performance ============

@router.get("/languages/performance")
async def get_language_performance(db: Session = Depends(get_db)):
    """
    Get performance metrics by language
    """
    languages = db.query(Language).all()
    
    language_stats = []
    
    for language in languages:
        courses = db.query(Course).filter(Course.language_id == language.id).all()
        course_ids = [c.id for c in courses]
        
        assessments = db.query(Assessment).filter(
            Assessment.course_id.in_(course_ids)
        ).all() if course_ids else []
        
        assessment_ids = [a.id for a in assessments]
        results = db.query(AssessmentResult).filter(
            AssessmentResult.assessment_id.in_(assessment_ids)
        ).all() if assessment_ids else []
        
        if results:
            avg_score = sum(r.percentage for r in results) / len(results)
            passed = sum(1 for r in results if r.status == "passed")
            passing_rate = (passed / len(results)) * 100
        else:
            avg_score = 0
            passing_rate = 0
        
        language_stats.append({
            "language": language.name,
            "courses": len(courses),
            "assessments": len(assessments),
            "total_attempts": len(results),
            "average_score": round(avg_score, 2),
            "passing_rate": round(passing_rate, 2)
        })
    
    return language_stats

# ============ Assessment Summary ============

@router.get("/assessments/summary")
async def get_assessments_summary(db: Session = Depends(get_db)):
    """
    Get summary of all assessments
    """
    weekly = db.query(Assessment).filter(
        Assessment.assessment_type == "weekly"
    ).count()
    monthly = db.query(Assessment).filter(
        Assessment.assessment_type == "monthly"
    ).count()
    yearly = db.query(Assessment).filter(
        Assessment.assessment_type == "yearly"
    ).count()
    
    # Active assessments (have pending results)
    active = db.query(Assessment).join(AssessmentResult).filter(
        AssessmentResult.status == "pending"
    ).distinct().count()
    
    return {
        "total_assessments": weekly + monthly + yearly,
        "weekly": weekly,
        "monthly": monthly,
        "yearly": yearly,
        "active": active
    }

# ============ Reports ============

@router.get("/reports/group-performance")
async def group_performance_report(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Generate group performance report
    """
    groups = db.query(Group).offset(skip).limit(limit).all()
    
    report = []
    for group in groups:
        assessment_ids = [a.id for a in group.assessments]
        results = db.query(AssessmentResult).filter(
            AssessmentResult.assessment_id.in_(assessment_ids)
        ).all() if assessment_ids else []
        
        if results:
            avg_score = sum(r.percentage for r in results) / len(results)
            passed = sum(1 for r in results if r.status == "passed")
        else:
            avg_score = 0
            passed = 0
        
        report.append({
            "group_id": group.id,
            "group_name": group.name,
            "employees": len(group.employees),
            "courses": len(group.courses),
            "assessments": len(group.assessments),
            "results": len(results),
            "passed": passed,
            "average_score": round(avg_score, 2)
        })
    
    return report

@router.get("/reports/employee-certification")
async def employee_certification_report(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Generate employee certification report
    """
    from app.models import Certification
    
    certifications = db.query(Certification).offset(skip).limit(limit).all()
    
    report = []
    for cert in certifications:
        employee = db.query(Employee).filter(Employee.id == cert.employee_id).first()
        course = db.query(Course).filter(Course.id == cert.course_id).first()
        
        report.append({
            "employee_code": employee.employee_code if employee else "N/A",
            "employee_name": employee.user.full_name if employee and employee.user else "N/A",
            "course_name": course.name if course else "N/A",
            "certificate_code": cert.certificate_code,
            "issued_date": cert.issued_date,
            "expiry_date": cert.expiry_date,
            "is_valid": cert.is_valid
        })
    
    return report
