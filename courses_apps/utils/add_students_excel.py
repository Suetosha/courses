import openpyxl
from django.contrib.auth import get_user_model


from courses_apps.users.models import Group
from courses_apps.utils.generate_password import generate_password
from courses_apps.utils.generate_username import generate_username

User = get_user_model()



# Функция для добавления студентов из эксель файла
def import_students_from_excel(excel_file):
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active

    # Пропускаем первую строку (заголовки)
    for row in sheet.iter_rows(min_row=2, values_only=True):
        first_name, last_name, group_number, year = row

        # Берем группу или её создаем
        group, created = Group.objects.get_or_create(number=group_number, year=year)

        # Генерация уникального username
        username = generate_username()

        # Генерация случайного пароля
        password = generate_password()


        # Создаем студента
        user = User.objects.create(
            username=username,
            last_name=last_name,
            first_name=first_name,
            role="student",

        )
        user.set_password(password)
        user.groups.add(group)
        user.save()