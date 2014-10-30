# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

from django.utils.encoding import smart_text

#Las funciones  de __str__ son el nombre con el que se representan en la pantalla de admin las filas de las tablas, por defecto diria
#"[Tabla.name] object"
class Currency(models.Model):
    currency = models.CharField(max_length=4)
    def __str__(self):
       return self.currency


class FinanceType(models.Model):
    type = models.CharField(max_length=20)
    def __str__(self):
        return self.type


class Finance(models.Model):
    id_application = models.ForeignKey('Application')
    id_finance_type = models.ForeignKey('FinanceType')
    id_currency = models.ForeignKey('Currency')
    amount = models.PositiveIntegerField()
    def get_finance_type(self):
        return self.id_finance_type.type


class Country(models.Model):
    country = models.CharField(max_length=100)
    def __str__(self):
       return self.country


class City(models.Model):
    country = models.ForeignKey('Country')
    city = models.CharField(max_length=100)
    def __str__(self):
       return self.city


class Destination(models.Model):
    application = models.ForeignKey('Application')
    country = models.CharField(max_length=55)
    city    = models.CharField(max_length=55)
    start_date = models.DateField()
    end_date   = models.DateField()
    def get_used_days(self):
        dt=self.end_date - self.start_date
        return dt.days


class CommissionType(models.Model):
    type = models.CharField(max_length=20)
    def __str__(self):
       return self.type


class Application(models.Model):
    id_Teacher = models.ForeignKey('Teacher')
    id_commission_type = models.ForeignKey('CommissionType')
    motive = models.TextField()
    financed_by = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    id_days_validation_state = models.ForeignKey('State', related_name='+')  # (?) related name because related name
    id_funds_validation_state = models.ForeignKey('State')
    directors_name = models.CharField(max_length=30)
    directors_rut = models.CharField(max_length=10)
    def __str__(self):
        return "Application "+str(self.id)
    #Obtiene el ultimo estado asociado a la solicitud
    def get_state(self):
        try:
            ret = ApplicationHasApplicationState.objects.filter(id_application=self.pk).order_by("date").reverse()[0].id_application_state
        except:
            print("Error in method get_state(). (models.py, Application)")
            ret = "Estado vacío, revisar"
        return ret
    #Obtiene la fecha del envio a facultad
    def sent_date(self):
        state = ApplicationState.objects.get(pk=2)
        applicationState = ApplicationHasApplicationState.objects.filter(id_application=self.pk,id_application_state=state)
        try:
            ret = applicationState[0].date
          #  ret = applicationState.order_by("date").reverse()[0].date
        except:
            ret = "No enviada"
        return ret
    def get_destinations(self):
        dests = Destination.objects.filter(application=self)
        return dests
    def get_used_days(self):
        dests=self.get_destinations()
        used_days=0
        for dest in dests:
            used_days+=dest.get_used_days()
        return used_days
    def get_documents(self):
        docs = Document.objects.filter(id_application=self)
        files =[]
        for doc in docs:
            files+=doc.file
        return files
    def get_replacements(self):
        replacements = Replacement.objects.filter(id_Application=self)
        return replacements
    def discount_days(self):
        if self.id_commission_type == CommissionType.objects.get(type="Academica"):
            return True
        return False
    def get_finances(self):
        finances=Finance.objects.filter(id_application=self)
        return finances

class ApplicationState(models.Model):
    state = models.CharField(max_length=20)
    def __str__(self):
        return self.state


class ApplicationHasApplicationState(models.Model):
    id_application = models.ForeignKey('Application')
    id_application_state = models.ForeignKey('ApplicationState')
    date = models.DateTimeField(auto_now_add=True, auto_now=False)


class Document(models.Model):
    id_application = models.ForeignKey('Application')
    file = models.FileField(blank=True, null=True,upload_to='documents')

class Hierarchy(models.Model):
    hierarchy = models.CharField(max_length=20)
    avaliable_days = models.IntegerField()
    def __str__(self):
        return self.hierarchy

class WorkingDay(models.Model):
    working_day=models.CharField(max_length=30)
    def __str__(self):
        return self.working_day

class Teacher(models.Model):
    user = models.OneToOneField(User)
    rut = models.CharField(max_length=10,unique=True)
    name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    signature = models.ImageField(max_length=255, blank=True, null=True, upload_to='signatures')
    mail = models.EmailField()
    hierarchy = models.ForeignKey('Hierarchy')      # jerarquia docente; Asistente(1), Asociado(2), Instructor(3)
    #full_teaching_time = models.BooleanField(default=True)      # jornada docente: True -> completa, False -> Media, el default es para que tenga algo y django no reclame
    working_day=models.ForeignKey('WorkingDay') #Jornada docente: Completa(1) Media (2)
    def __str__(self):
        return self.name + " " + self.last_name
    def get_courses(self):
        his_courses = TeacherHasCourse.objects.filter(id_Teacher=self)
        #if len(his_courses)==1:
        #    his_courses=[his_courses]
        courses = []
        for course in his_courses:
            courses=courses+[course.id_Course]
        return courses
    def get_modules(self):
        courses = self.get_courses()
        modules = []
        for course in courses:
            modules+=(course.get_modules())
        return modules
    def get_applications(self):
        his_applications = Application.objects.filter(id_Teacher=self)
        return his_applications
    def get_used_days(self):
        his_apps = self.get_applications()
        used_days=0
        for app in his_apps:
            if app.discount_days():
                used_days+=app.get_used_days()
        return used_days
    def get_avaliable_days(self):
        used_days=self.get_used_days()
        if used_days<14:
            return self.hierarchy.avaliable_days-used_days
        else:
            return "ha superado la cantidad máxima de semanas docentes que puede ausentarse, contáctese con jefa de estudios."

    def get_possible_replacement_teachers(self):
        y_modules=self.get_modules()
        my_modules=set(y_modules)
        replacement=[('','--------')]
        teachers = Teacher.objects.all()
        i=1
        for teacher in teachers:
            their_modules=set(teacher.get_modules())
            if my_modules.isdisjoint(their_modules):
                replacement.append((teacher.pk,teacher))
                i+=1
        return replacement

#rut_teacher es un Teacher no un rut!!!
class Replacement(models.Model):
    rut_teacher = models.ForeignKey('Teacher')
    id_Application = models.ForeignKey('Application')
    answer_date = models.DateTimeField(blank=True, null=True)
    type = models.ForeignKey('ReplacementType')
    id_state = models.ForeignKey('State')
    def get_appliant_teacher(self):
        return self.id_Application.id_Teacher


class State(models.Model):
    state = models.CharField(max_length=16)
    def __str__(self):
        return self.state


class InactivePeriod(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()  # blank=True, null=True
    description = models.TextField(blank=True, null=True)


class Course(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=8)
    section = models.IntegerField(max_length=2)
    def __str__(self):
        return self.name
    def get_modules(self):
        its_modules = CourseHasModule.objects.filter(id_Course=self)
        modules=[]
        for module in its_modules:
            modules=modules+[module.id_Module]
        return modules


class Module(models.Model):
    block = models.CharField(max_length=3)
    def __str__(self):
        return self.block


class CourseHasModule(models.Model):
    id_Course = models.ForeignKey('Course')
    id_Module = models.ForeignKey('Module')


class TeacherHasCourse(models.Model):
    id_Teacher = models.ForeignKey('Teacher')
    id_Course = models.ForeignKey('Course')
    def __str__(self):
        return str(self.id_Teacher) + str("/")+ str(self.id_Course)

class ReplacementType(models.Model):
    type = models.CharField(max_length=20)
    def __str__(self):
        return self.type
