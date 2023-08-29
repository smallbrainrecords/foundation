from collections import OrderedDict
from django.db import connection
import logging
from apps.todo_app.todo_problems import serializers as problem_serializer

def get_todo_problem(problem_id):
    problem_dict = {}
    with connection.cursor() as problem_cursor:
        problem_cursor.execute(
            """
            SELECT ep.*
            FROM emr_problem ep 
            WHERE id = %s;
            """, [problem_id])
        
        for row in problem_cursor.fetchall():
            row_data = OrderedDict(
                zip([col[0] for col in problem_cursor.description], row)
            )
            problem_dict = problem_serializer.serialize_todo_problem(row_data)            
            
        problem_cursor.execute(
            """
            SELECT *
            FROM emr_problemsegment ep 
            WHERE problem_id = %s;
            """, [problem_id])
        
        problem_segments = []
        problem_seg_results = problem_cursor.fetchall()
        
        if problem_seg_results:
            for row in problem_seg_results:
                row_data = OrderedDict(
                    zip([col[0] for col in problem_cursor.description], row)
                )
                
                problem_segments.append(problem_serializer.serialize_todo_problem_segment(
                    row_data
                ))
            
            problem_dict["problem_segment"] = problem_segments
        
        problem_cursor.execute(
            """
            SELECT ep.*,
                au.first_name  as author_first_name,
                au.last_name  as author_last_name,
                au.username  as author_username,
                au.email as author_email,
                eu.role as author_role,
                au.is_active as author_is_active,
                pat.first_name  as patient_first_name,
                pat.last_name  as patient_last_name,
                pat.username  as patient_user_name,
                pat.email as patient_email,
                pp.role as patient_role,
                pat.is_active as patient_is_active
            FROM emr_problem_labels epl
            JOIN emr_problemlabel ep on
                epl.problemlabel_id = ep.id
            JOIN auth_user au on
                ep.author_id = au.id
            JOIN emr_userprofile eu on
                au.id = eu.id
            JOIN auth_user pat on
                ep.patient_id = pat.id
            JOIN emr_userprofile pp on
                pat.id = pp.id
            WHERE problem_id = %s;
            """, [problem_id])
        
        problem_labels = []
        for row in problem_cursor.fetchall():
            row_data = OrderedDict(
                zip([col[0] for col in problem_cursor.description], row)
            )
            
            problem_labels.append(problem_serializer.serialize_todo_problem_label(
                row_data
            ))
        
        problem_dict["labels"] = problem_labels
        problem_cursor.close()
    
    # need to understand what's being done here
    with connection.cursor() as problem_effected_cursor:
        problem_effected_cursor.execute(
            """
            SELECT epr.source_id
            FROM emr_problemrelationship epr
            WHERE target_id = %s;
            """, [problem_id])
        
        problem_effected_result = problem_effected_cursor.fetchall()
        problem_effected_list = []
        if problem_effected_result:
            for row in problem_seg_results:
                problem_effected_list.append(row[0])
        # problem_dict["effected"] = problem_effected_list
        
        problem_effected_cursor.close()
        
    with connection.cursor() as problem_effecting_cursor:
        problem_effecting_cursor.execute(
            """
            SELECT epr.target_id
            FROM emr_problemrelationship epr
            WHERE source_id = %s;
            """, [problem_id])
        
        problem_effecting_result = problem_effecting_cursor.fetchall()
        problem_effecting_list = []
        if problem_effecting_result:
            for row in problem_seg_results:
                problem_effecting_list.append(row[0])
        # problem_dict["effecting"] = problem_effecting_list 
                
        problem_effecting_cursor.close()
        
    return problem_dict
        
    
        
        