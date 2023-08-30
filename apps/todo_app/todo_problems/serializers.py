

from collections import OrderedDict
import logging


def serialize_todo_problem(problem_row_data):
    problem_dict = {
        "id": problem_row_data["id"],
        "problem_segment": [],
        "patient": problem_row_data["patient_id"],
        "parent": problem_row_data["parent_id"],
        "labels": [],
        "problem_name": problem_row_data["problem_name"],
        "old_problem_name": problem_row_data["old_problem_name"],
        "concept_id": problem_row_data["concept_id"],
        "is_controlled": bool(problem_row_data["is_controlled"]),
        "is_active": bool(problem_row_data["is_active"]),
        "authenticated": bool(problem_row_data["authenticated"]),
        "start_time": problem_row_data["start_date"].strftime("%H:%M:%S"),
        "start_date": problem_row_data["start_date"].strftime("%m/%d/%Y"),
        "effected": [],
        "effecting": []
    }
    return OrderedDict(problem_dict)


def serialize_todo_problem_segment(row_data):
    problem_segment_dict = {
        "id": row_data["id"],
        "problem": row_data["problem_id"],
        "is_controlled": bool(row_data["is_controlled"]),
        "is_active": bool(row_data["is_active"]),
        "authenticated": bool(row_data["authenticated"]),
        "event_id": row_data["event_id"],
        "start_time": row_data["start_date"].strftime("%H:%M:%S"),
        "start_date": row_data["start_date"].strftime("%m/%d/%Y"),
    }
    
    return OrderedDict(problem_segment_dict)


def serialize_todo_problem_label(row_data):
    problem_label_author = {
        "id": row_data["author_id"],
        "first_name": row_data["author_first_name"],
        "last_name": row_data["author_last_name"],
        "username": row_data["author_username"],
        "email": row_data["author_email"],
        "profile": {
            "id": row_data["author_id"],
            "user": row_data["author_id"],
            "role": row_data["author_role"],
        },
        "is_active": row_data["author_is_active"],
    }
    
    problem_label_patient = {
        "id": row_data["author_id"],
        "first_name": row_data["author_first_name"],
        "last_name": row_data["author_last_name"],
        "username": row_data["author_username"],
        "email": row_data["author_email"],
        "profile": {
            "id": row_data["author_id"],
            "user": row_data["author_id"],
            "role": row_data["author_role"],
        },
        "is_active": row_data["author_is_active"],
    }
    
    problem_label_dict = {
        "id": row_data["id"],
        "name": row_data["name"],
        "css_class": row_data["css_class"],
        "author": OrderedDict(problem_label_author),
        "patient": OrderedDict(problem_label_patient),
    }
    
    return OrderedDict(problem_label_dict)