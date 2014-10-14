from django.shortcuts import render, render_to_response, RequestContext

from salidas.models import *    #  for data
from salidas.forms import *     #  for calendar
from salidas.calendar import *  #  for calendar
from django.utils.safestring import mark_safe   #  for calendar
from django.contrib import auth
from django.contrib.auth import  authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test,permission_required

# Views for all users
def home(request):
    return render_to_response("login.html", locals(), context_instance=RequestContext(request))


def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = auth.authenticate(username=username,password=password)
    if user is not None and user.is_active:
        # Clave correcta, y el usuario está marcado "activo"
        login(request, user)
        # Redirigir a una página de éxito.

        return redirect(new_application)
    else:
        # Mostrar una página de error
        return redirect(login)


#Views for teachers
def new_application(request):
    application = NewApplicationForm(request.POST or None)
    destinationFormSet = DestinationFormSet(request.POST or None)
    academicReplacement = ReplacementApplicationForm(request.POST or None)
    executiveReplacement = ReplacementApplicationForm(request.POST or None)
    if application.is_valid():
        new_app = application.save(commit=False)
        new_app.save()
    if destinationFormSet.is_valid():
        new_destination = destinationFormSet.save(commit=False)
        new_destination.save()
    if academicReplacement.is_valid():
        replacement = academicReplacement.save(commit=False)
        replacement.save()
    if executiveReplacement.is_valid():
        replacement = executiveReplacement.save(commit=False)
        replacement.save()
    return render_to_response("new_application_form.html", locals(), context_instance=RequestContext(request))


def prueba(request):
    application = NewApplicationForm(request.POST or None)
    if application.is_valid():
        rut1 = application.cleaned_data['rut']
        ct = application.cleaned_data['id_commission_type']
        fb = application.cleaned_data['financed_by']
        motive = application.cleaned_data['motive']
        daysv = State.objects.get(pk=2)
        faysv = State.objects.get(pk=2)
        newApp = Application(rut=rut1,id_commission_type=ct,financed_by=fb,motive=motive,id_days_validation_state=daysv,id_funds_validation_state=faysv)
        newApp.save()
        return render_to_response("login.html",locals(),)
    return render_to_response("prueba.html", locals(), context_instance=RequestContext(request))


def teacher_calendar(request):
    return render_to_response("teacher_calendar.html", locals(), context_instance=RequestContext(request))


# Views for administrative people
def list_of_applications(request):
    apps = Application.objects.all()
    return render_to_response("list_of_applications.html", locals(), context_instance=RequestContext(request))


def application_detail(request):
    id_app = 1  #  IMPORTANTE! : este valor debe ser el id de la solicitud seleccionada!
    query = Application.objects.get(pk = id_app)  # Application query
    profesor = query.rut

    comm_type = query.id_commission_type
    dest = Destination.objects.filter(application = query.id)
    return render_to_response("application_detail.html", locals(), context_instance=RequestContext(request))


def historic_calendar(request):
    return render_to_response("historic_calendar.html", locals(), content_type=RequestContext(request))


def list_alejandro(request):
    apps = Application.objects.all()
    return render_to_response("list_alejandro.html", locals(), context_instance=RequestContext(request))


def detail_alejandro(request):
    id_app = 1  #  IMPORTANTE! : este valor debe ser el id de la solicitud seleccionada!
    application = Application.objects.get(pk = id_app)
    destinations = Destination.objects.filter(application = id_app)
    teacher = application.rut
    return render_to_response("detail_alejandro.html", locals(), content_type=RequestContext(request))

# Aditional views
def calendar(request, year, month):
    # primero debemos obtenemos los datos de la base de datos, luego le damos la query a WorkoutCalendar
    # un ejemplo de cómo hacer esto es el que se muestra a continuación.

    # para ver el resultado o mas detalles de como se supone funciona esto, revisar el siguiente link
    #   http://uggedal.com/journal/creating-a-flexible-monthly-calendar-in-django/

    '''
    my_workouts = Workouts.objects.order_by('my_date').filter(
        my_date__year=year, my_date__month=month
    )

    cal = WorkoutCalendar(my_workouts).formatmonth(year, month)
    return render_to_response('my_template.html', {'calendar': mark_safe(cal),})  # para nuestro caso, no sé bien qué deberíamos retornar.
    '''

