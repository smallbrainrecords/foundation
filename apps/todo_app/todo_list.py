from collections import OrderedDict
from django.db import connection
import logging

from apps.todo_app import custom_serializers
from apps.todo_app.todo_problems import operations as prob_operations


def get_todo_list_from_label(label_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                et.*,
                au.*
            FROM
                emr_todo et
            JOIN emr_todo_labels etl ON
                et.id = etl.todo_id
            JOIN auth_user au ON
                au.id = et.patient_id
            JOIN emr_label el ON
                el.id = etl.label_id
            WHERE
                el.id IN %s;
            """, [label_ids])
        
        todo_results = []
        for row in cursor.fetchall():
            todo_dict = custom_serializers.serialize_todo(row, cursor.description)
            todo_dict["patient"] = custom_serializers.serialize_todo_patient(
                row, cursor.description
            )
            
            if todo_dict["problem"]:
                problem_dict = prob_operations.get_todo_problem(todo_dict["problem"])
                todo_dict["problem"] = problem_dict
                
            todo_dict["labels"] = get_todo_labels(todo_dict["id"])
            todo_dict["attachments"] = get_todo_attachments(todo_dict["id"])
            todo_dict["comments"] = get_todo_attachments(todo_dict["id"])
            todo_dict["members"] = get_todo_members(todo_dict["id"])

            todo_results.append(todo_dict)
            
        cursor.close()
            
        return todo_results
    
    

def get_todo_labels(todo_id):
    
    with connection.cursor() as todo_label_cursor:
        
        todo_label_cursor.execute(
            """
            SELECT el.id,
                el.name,
                el.css_class,
                el.is_all,
                au.id as author_id,
                au.first_name  as author_first_name,
                au.last_name  as author_last_name,
                au.username  as author_username,
                au.email as author_email,
                eu.role as author_role,
                au.is_active as author_is_active
            FROM emr_todo_labels etl
            JOIN emr_label el ON
                etl.label_id = el.id
            JOIN auth_user au ON
                el.author_id = au.id
            JOIN emr_userprofile eu on
                au.id = eu.id
            WHERE todo_id = %s;
            """, [todo_id])
        
        todo_labels = []
        todo_labels_results = todo_label_cursor.fetchall()
        
        if todo_labels_results:
            for row in todo_labels_results:
                row_data = OrderedDict(
                    zip([col[0] for col in todo_label_cursor.description], row)
                )
                
                todo_labels.append(custom_serializers.serialize_todo_label(
                    row_data
                ))
                
        todo_label_cursor.close()
                
        return todo_labels
    
    
def get_todo_attachments(todo_id):
    with connection.cursor() as todo_attachment_cursor:
        
        todo_attachment_cursor.execute(
            """
            SELECT eat.id as attachment_id,
                au.id as user_id,
                au.first_name,
                au.last_name,
                au.username,
                au.email,
                eu.role,
                au.is_active,
                eat.attachment,
                eat.datetime
            FROM emr_todoattachment eat
            JOIN auth_user au ON
                eat.user_id = au.id
            JOIN emr_userprofile eu ON
                au.id = eu.id
            WHERE todo_id = %s;
            """, [todo_id])
        
        todo_attachments = []
        todo_attachments_results = todo_attachment_cursor.fetchall()
        
        if todo_attachments_results:
            for row in todo_attachments_results:
                row_data = OrderedDict(
                    zip([col[0] for col in todo_attachment_cursor.description], row)
                )
                
                todo_attachments.append(custom_serializers.serialize_todo_attachment(
                    row_data
                ))
                
        todo_attachment_cursor.close()
                
        return todo_attachments
    

def get_todo_comments(todo_id):
    with connection.cursor() as todo_comments_cursor:  
        todo_comments_cursor.execute(
            """
            SELECT et.id as comment_id,
                et.comment,
                et.datetime,
                au.id as user_id,
                au.first_name,
                au.last_name,
                au.username,
                au.email,
                eu.role,
                au.is_active
            FROM emr_todocomment et
            JOIN auth_user au ON
                et.user_id = au.id
            JOIN emr_userprofile eu ON
                au.id = eu.id
            WHERE todo_id = %s;
            """, [todo_id])
        
        todo_comments = []
        todo_comments_results = todo_comments_cursor.fetchall()
        
        if todo_comments_results:
            for row in todo_comments_results:
                row_data = OrderedDict(
                    zip([col[0] for col in todo_comments_cursor.description], row)
                )
                
                todo_comments.append(custom_serializers.serialize_todo_comments(
                    row_data
                ))
                
        todo_comments_cursor.close()
                
        return todo_comments
    
    
def get_todo_members(todo_id):
    with connection.cursor() as todo_members_cursor:  
        todo_members_cursor.execute(
            """
            SELECT *
            FROM emr_taggedtodoorder et 
            JOIN auth_user au ON
                et.user_id = au.id
            JOIN emr_userprofile eu ON
                au.id = eu.id
            WHERE todo_id = %s;
            """, [todo_id])
        
        todo_members = []
        todo_members_results = todo_members_cursor.fetchall()
        
        if todo_members_results:
            for row in todo_members_results:
                row_data = OrderedDict(
                    zip([col[0] for col in todo_members_cursor.description], row)
                )
                
                todo_members.append(custom_serializers.serialize_todo_member(
                    row_data
                ))
                
        todo_members_cursor.close()
                
        return todo_members

            