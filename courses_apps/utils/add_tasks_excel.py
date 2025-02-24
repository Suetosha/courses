import openpyxl
from courses_apps.tests.models import Task, Answer
from django.db import transaction



def import_tasks_from_excel(file):
    try:
        wb = openpyxl.load_workbook(file)
        sheet = wb.active

        # Группируем операции в транзакцию
        with transaction.atomic():
            for row_index, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    question_text = str(row[0]).strip() if row[0] else None
                    if not question_text:
                        raise ValueError(f"Ошибка в строке {row_index}: вопрос не может быть пустым.")

                    is_text_input = bool(row[1]) if row[1] else False
                    is_multiple_choice = bool(row[2]) if row[2] else False
                    is_compiler = bool(row[3]) if row[3] else False
                    correct_answers = str(row[4]).split() if row[4] else []

                    if is_text_input or is_compiler:
                        if len(correct_answers) > 1:
                            raise ValueError(
                                f"Ошибка в строке {row_index}: при is_text_input или is_compiler должен быть только один правильный ответ.")

                    # Создаём задание
                    task = Task.objects.create(
                        question=question_text,
                        is_text_input=is_text_input,
                        is_multiple_choice=is_multiple_choice,
                        is_compiler=is_compiler
                    )

                    # Добавляем ответы
                    has_correct_answer = False
                    for idx, answer_text in enumerate(row[5:], start=1):

                        # Если поле ответа не пустое
                        if answer_text:
                            is_correct = str(idx) in correct_answers
                            if is_correct:
                                has_correct_answer = True
                            Answer.objects.create(
                                task=task,
                                text=str(answer_text).strip(),
                                is_correct=is_correct
                            )

                    if not has_correct_answer:
                        raise ValueError(f"Ошибка в строке {row_index}: должен быть хотя бы один правильный ответ.")

                except ValueError as e:
                    raise ValueError(f"Ошибка в строке {row_index}: {e}")

    except Exception as e:
        raise Exception(f"Ошибка обработки файла: {str(e)}")
