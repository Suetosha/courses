import openpyxl
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from courses_apps.users.models import Group, User
from courses_apps.utils.generate_password import generate_password


# Функция для создания эксель файла по студентам из определенной группы
def generate_excel(group_number, year):
    group = Group.objects.get(number=group_number, year=year)
    students = User.objects.filter(groups=group)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students List"
    ws.append(['Логин', 'Фамилия', 'Имя', 'Группа', 'Год', 'Пароль'])

    for student in students:
        for group in student.groups.all():
            # Генерация временного пароля
            temp_password = generate_password()

            # Сохраняем новый пароль в базе данных
            student.password = make_password(temp_password)
            student.save()

            # Добавляем данные в Excel
            ws.append(
                [student.username, student.last_name, student.first_name, group.number, group.year, temp_password])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="students_{group_number}_{year}.xlsx"'
    wb.save(response)

    return response
