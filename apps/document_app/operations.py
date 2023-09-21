"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from common.views import timeit


#@timeit
def fetch_document_label_set(document):
    """
    Load all labels associated with a document which either direct pinned to this document or label via pinned todo
    TODO: Remove duplicate label
    :param document:
    :return:
    """
    document_todo_label_set = []
    document_label_set = document.labels.all()
    document_todo_set = document.todos.all()
    for document_todo in document_todo_set:
        if document_todo.labels.count() != 0:
            document_todo_label_set += document_todo.labels.all()

    return set(list(document_label_set) + list(document_todo_label_set))
