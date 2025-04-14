from courses_apps.tests.models import Answer
from courses_apps.utils.compiler import run_code

# Функция подсчёта результатов прохождения теста
# tasks - Список всех заданий
# user_answers - Словарь с данными пользователя из заполненной формы
def calculate_test_result(tasks, user_answers):
    total_score = 0
    max_score = 0

    # Проверяем каждую задачу
    for task in tasks:
        max_score += task.point
        # Получаем правильные ответы для задания
        answers = Answer.objects.filter(task=task)

        # Получаем ответ пользователя для задачи
        user_answer = user_answers.get(str(task.id))
        if user_answer is None:
            continue

        # Если задание с компилятором
        if task.is_compiler:
            correct_answer = answers.filter(is_correct=True).first().text
            # Результат выполнения кода
            user_result = run_code(user_answer)
            if user_result == correct_answer:
                total_score += task.point

        elif task.is_text_input:
            correct_answer = answers.filter(is_correct=True).first().text
            if user_answer == correct_answer:
                total_score += task.point

        # Если задание с множественным выбором
        elif task.is_multiple_choice:
            user_correct_answers = 0
            correct_answers = answers.filter(is_correct=True)
            total_answers = correct_answers.count()

            for answer in correct_answers:
                if str(answer.id) in user_answer:
                    user_correct_answers += 1

            if total_answers > 0:
                user_correct_count = user_correct_answers / total_answers
                if user_correct_count > 0.5:
                    total_score += task.point
                else:
                    total_score += 0.5 * task.point

        # Если задание с радио баттоном
        else:
            correct_answer = answers.filter(is_correct=True).first()
            if user_answer == str(correct_answer.id):
                total_score += task.point

    # Подсчет процента успешности
    score_percent = int((total_score / max_score) * 100) if max_score > 0 else 0

    # Оценка на основе процента
    if score_percent < 50:
        result = "Не сдал"
    elif 50 <= score_percent <= 60:
        result = "Удовлетворительно"
    elif 61 <= score_percent <= 85:
        result = "Хорошо"
    else:
        result = "Отлично"

    return {
        # Набранные баллы
        "total_score": total_score,
        # Максимально возможные баллы
        "max_score": max_score,
        # Процент успешности
        "score_percent": score_percent,
        # Итог (текстовая оценка)
        "result": result
    }
