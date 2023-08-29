

from collections import OrderedDict
import logging


def serialize_todo_patient(row_data, cursor_description):
    row_dict = OrderedDict(zip([col[0] for col in cursor_description], row_data))
    patient_dict = {
        "id": row_dict["patient_id"],
        "first_name": row_dict["first_name"],
        "last_name": row_dict["last_name"],
        "username": row_dict["username"],
        "email": row_dict["email"],
        "profile": {
            "id": row_dict["patient_id"],
            "user": row_dict["patient_id"],
            "role": "patient"
        },
        "is_active": bool(row_dict["is_active"]),
    }
    return patient_dict


def serialize_todo(row_data, cursor_description):
    row_dict = OrderedDict(zip([col[0] for col in cursor_description], row_data))
    if row_dict.get("due_date"):
        due_date = row_dict["due_date"].strftime("%m/%d/%Y, %H:%M:%S")
    if row_dict.get("created_on"):
        created_on = row_dict["created_on"].strftime("%m/%d/%Y, %H:%M:%S")
    
    todo_dict = {
        "id": row_dict["patient_id"],
        "patient": {},
        "user": row_dict["user_id"],
        "problem": row_dict["problem_id"],
        "todo": row_dict["todo"],
        "accomplished": bool(row_dict["accomplished"]),
        "due_date": due_date if row_dict.get("due_date") else "",
        "labels": [],
        "comments": [],
        "attachments": [],
        "members": [],
        "document_set": [],
        "a1c": row_dict["a1c_id"],
        "colon_cancer": row_dict["colon_cancer_id"],
        "created_at": row_dict["created_at"],
        "created_on": created_on if row_dict.get("created_on") else "",
    }
    
    return OrderedDict(todo_dict)


def serialize_todo_label(row_data):
    todo_label_author = {
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
    
    todo_label_dict = {
        "id": row_data["id"],
        "name": row_data["name"],
        "css_class": row_data["css_class"],
        "author": OrderedDict(todo_label_author),
    }
    
    return OrderedDict(todo_label_dict)


def serialize_todo_attachment(row_data):
    todo_attachment_user = {
        "id": row_data["user_id"],
        "first_name": row_data["first_name"],
        "last_name": row_data["last_name"],
        "username": row_data["username"],
        "email": row_data["email"],
        "profile": {
            "id": row_data["user_id"],
            "user": row_data["user_id"],
            "role": row_data["role"],
        },
        "is_active": row_data["is_active"],
    }
    if row_data.get("datetime"):
        datetime = row_data["datetime"].strftime("%m/%d/%Y, %H:%M:%S")
        
    attachment_split = row_data["attachment"].split("/")
    filename = attachment_split[-1]
    filename_split = filename.split(".")
    filename_ext = filename_split[-1]
    image_extensions = ['jpg', 'png', 'jpeg']
        
    todo_attachment_dict = {
        "id": row_data["attachment_id"],
        "user": OrderedDict(todo_attachment_user),
        "attachment": row_data["attachment"],
        "datetime": datetime if row_data.get("datetime") else "",
        "filename": filename,
        "is_image": bool(filename_ext in image_extensions)
    }
    
    return OrderedDict(todo_attachment_dict)


def serialize_todo_comments(row_data):
    todo_comment_user = {
        "id": row_data["user_id"],
        "first_name": row_data["first_name"],
        "last_name": row_data["last_name"],
        "username": row_data["username"],
        "email": row_data["email"],
        "profile": {
            "id": row_data["user_id"],
            "user": row_data["user_id"],
            "role": row_data["role"],
        },
        "is_active": row_data["is_active"],
    }
    if row_data.get("datetime"):
        datetime = row_data["datetime"].strftime("%m/%d/%Y, %H:%M:%S")
        
    todo_attachment_dict = {
        "id": row_data["comment_id"],
        "user": OrderedDict(todo_comment_user),
        "comment": row_data["comment"],
        "datetime": datetime if row_data.get("datetime") else "",
    }
    
    return OrderedDict(todo_attachment_dict)


def serialize_todo_member(row_data):
    todo_comment_user = {
        "id": row_data["user_id"],
        "first_name": row_data["first_name"],
        "last_name": row_data["last_name"],
        "username": row_data["username"],
        "email": row_data["email"],
        "profile": {
            "id": row_data["user_id"],
            "user": row_data["user_id"],
            "role": row_data["role"],
        },
        "is_active": row_data["is_active"],
    }
    
    return OrderedDict(todo_comment_user)