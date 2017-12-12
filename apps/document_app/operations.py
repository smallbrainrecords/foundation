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
