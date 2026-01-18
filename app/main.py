from fastapi import FastAPI, HTTPException
from bson import ObjectId
from app.db import db
from app.schemas import StudentCreate
from fastapi import FastAPI, HTTPException, Query


app = FastAPI(title="StudyTrack API")

students_col = db["students"]
def to_student(doc):
    return {
        "id": str(doc["_id"]),
        "firstName": doc["firstName"],
        "lastName": doc["lastName"],
        "email": doc["email"],
        "program": doc.get("program", ""),
        "school": doc.get("school", "EMSI"),
        "timezone": doc.get("timezone", "Africa/Casablanca"),
        "role": doc.get("role", "student"),
        "createdAt": doc.get("createdAt"),
        "updatedAt": doc.get("updatedAt"),
    }

@app.get("/")
def root():
    return {"message": "StudyTrack API running ✅"}

@app.get("/health")
def health():
    db.command("ping")
    return {"status": "ok", "mongo": "connected"}

# ✅ CREATE student
@app.post("/students")
def create_student(payload: StudentCreate):
    # check unique email (since your DB unique index may not exist due to disk issue)
    if students_col.find_one({"email": payload.email}):
        raise HTTPException(status_code=409, detail="Email already exists")

    doc = payload.model_dump()
    doc["createdAt"] = __import__("datetime").datetime.utcnow()
    doc["updatedAt"] = __import__("datetime").datetime.utcnow()

    result = students_col.insert_one(doc)
    created = students_col.find_one({"_id": result.inserted_id})
    return to_student(created)

# ✅ READ all students
@app.get("/students")
def list_students():
    return [to_student(s) for s in students_col.find().limit(100)]

# ✅ READ one student
@app.get("/students/{student_id}")
def get_student(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = students_col.find_one({"_id": ObjectId(student_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
    return to_student(doc)

# ✅ DELETE student
@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    if not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    res = students_col.delete_one({"_id": ObjectId(student_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"deleted": True}

from app.schemas import SessionCreate
sessions_col = db["sessions"]

def to_session(doc):
    return {
        "id": str(doc["_id"]),
        "studentId": str(doc["studentId"]),
        "subjectId": str(doc["subjectId"]),
        "startedAt": doc["startedAt"],
        "durationMin": doc["durationMin"],
        "difficulty": doc["difficulty"],
        "mood": doc["mood"],
        "period": doc["period"],
        "type": doc["type"],
        "tags": doc.get("tags", []),
        "notes": doc.get("notes"),
    }

@app.post("/sessions")
def create_session(payload: SessionCreate):
    from bson import ObjectId
    from fastapi import HTTPException

    if not ObjectId.is_valid(payload.studentId) or not ObjectId.is_valid(payload.subjectId):
        raise HTTPException(status_code=400, detail="Invalid studentId/subjectId")

    doc = payload.model_dump()
    doc["studentId"] = ObjectId(payload.studentId)
    doc["subjectId"] = ObjectId(payload.subjectId)
    doc["createdAt"] = __import__("datetime").datetime.utcnow()
    doc["updatedAt"] = __import__("datetime").datetime.utcnow()

    result = sessions_col.insert_one(doc)
    created = sessions_col.find_one({"_id": result.inserted_id})
    return to_session(created)

@app.get("/sessions")
def list_sessions(limit: int = 100):
    limit = min(max(limit, 1), 200)
    return [to_session(s) for s in sessions_col.find().sort("startedAt", -1).limit(limit)]

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    from bson import ObjectId
    from fastapi import HTTPException
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    doc = sessions_col.find_one({"_id": ObjectId(session_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    return to_session(doc)


from fastapi import Query

@app.get("/sessions-enriched")
def list_sessions_enriched(limit: int = Query(default=50, ge=1, le=200)):
    pipeline = [
        {"$sort": {"startedAt": -1}},
        {"$limit": limit},

        {"$lookup": {
            "from": "students",
            "localField": "studentId",
            "foreignField": "_id",
            "as": "student"
        }},
        {"$lookup": {
            "from": "subjects",
            "localField": "subjectId",
            "foreignField": "_id",
            "as": "subject"
        }},

        {"$project": {
            "_id": 1,
            "startedAt": 1,
            "durationMin": 1,
            "difficulty": 1,
            "mood": 1,
            "period": 1,
            "type": 1,
            "tags": {"$ifNull": ["$tags", []]},
            "notes": 1,

            # student name safe
            "studentFirst": {"$ifNull": [{"$arrayElemAt": ["$student.firstName", 0]}, "Unknown"]},
            "studentLast": {"$ifNull": [{"$arrayElemAt": ["$student.lastName", 0]}, "Student"]},

            # subject name safe
            "subjectName": {"$ifNull": [{"$arrayElemAt": ["$subject.name", 0]}, "Unknown subject"]}
        }}
    ]

    rows = list(db["sessions"].aggregate(pipeline))

    # Convert ObjectId to string safely in Python (no $toString needed)
    result = []
    for r in rows:
        result.append({
            "id": str(r.get("_id")),
            "student": f"{r.get('studentFirst')} {r.get('studentLast')}",
            "subject": r.get("subjectName"),
            "startedAt": r.get("startedAt"),
            "durationMin": r.get("durationMin"),
            "difficulty": r.get("difficulty"),
            "mood": r.get("mood"),
            "period": r.get("period"),
            "type": r.get("type"),
            "tags": r.get("tags", []),
            "notes": r.get("notes"),
        })
    return result


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    from bson import ObjectId
    from fastapi import HTTPException
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid id")
    res = sessions_col.delete_one({"_id": ObjectId(session_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}

from app.schemas import SubjectCreate
subjects_col = db["subjects"]

def to_subject(doc):
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "program": doc["program"],
        "coefficient": doc.get("coefficient"),
        "color": doc.get("color"),
    }

@app.get("/subjects")
def list_subjects():
    return [to_subject(s) for s in subjects_col.find().limit(200)]

@app.post("/subjects")
def create_subject(payload: SubjectCreate):
    doc = payload.model_dump()
    doc["createdAt"] = __import__("datetime").datetime.utcnow()
    doc["updatedAt"] = __import__("datetime").datetime.utcnow()
    res = subjects_col.insert_one(doc)
    created = subjects_col.find_one({"_id": res.inserted_id})
    return to_subject(created)

@app.get("/analytics/time-by-subject")
def time_by_subject():
    pipeline = [
        {"$group": {"_id": "$subjectId", "totalMinutes": {"$sum": "$durationMin"}}},
        {"$sort": {"totalMinutes": -1}},
        {"$lookup": {"from": "subjects", "localField": "_id", "foreignField": "_id", "as": "subject"}},
        {"$unwind": "$subject"},
        {"$project": {"_id": 0, "subject": "$subject.name", "totalMinutes": 1}}
    ]
    return list(db["sessions"].aggregate(pipeline))

@app.get("/analytics/time-by-period")
def time_by_period():
    pipeline = [
        {"$group": {"_id": "$period", "totalMinutes": {"$sum": "$durationMin"}}},
        {"$sort": {"totalMinutes": -1}},
        {"$project": {"_id": 0, "period": "$_id", "totalMinutes": 1}}
    ]
    return list(db["sessions"].aggregate(pipeline))

@app.get("/analytics/difficulty-by-subject")
def difficulty_by_subject():
    pipeline = [
        {"$group": {"_id": "$subjectId", "avgDifficulty": {"$avg": "$difficulty"}}},
        {"$sort": {"avgDifficulty": -1}},
        {"$lookup": {"from": "subjects", "localField": "_id", "foreignField": "_id", "as": "subject"}},
        {"$unwind": "$subject"},
        {"$project": {"_id": 0, "subject": "$subject.name", "avgDifficulty": {"$round": ["$avgDifficulty", 2]}}}
    ]
    return list(db["sessions"].aggregate(pipeline))

from fastapi import Query

@app.get("/analytics/time-by-student")
def time_by_student():
    pipeline = [
        {"$group": {"_id": "$studentId", "totalMinutes": {"$sum": "$durationMin"}}},
        {"$sort": {"totalMinutes": -1}},
        {"$lookup": {"from": "students", "localField": "_id", "foreignField": "_id", "as": "student"}},
        {"$unwind": "$student"},
        {"$project": {"_id": 0, "student": {"$concat": ["$student.firstName", " ", "$student.lastName"]}, "totalMinutes": 1}}
    ]
    return list(db["sessions"].aggregate(pipeline))
