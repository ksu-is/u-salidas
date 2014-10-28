from django.shortcuts import render, render_to_response, RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.contrib import auth
from django.shortcuts import render,render_to_response,redirect,get_object_or_404
from django.contrib.auth import  authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test,permission_required
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm

from django.utils.safestring import mark_safe   #  for calendar

from salidas.models import *
from django.contrib.auth.models import User,Group

from salidas.forms import *     #  for calendar
from salidas.calendar import *  #  for calendar


# Views for all users
# Login
def home(request):
    return render_to_response("General/login.html", locals(), context_instance=RequestContext(request))

def is_in_group(user, group):
	users_in_group = Group.objects.get(name=group).user_set.all()
	if user in users_in_group or user.is_superuser:
		return True
	else:
		return False


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = auth.authenticate(username=username,password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                if is_in_group(user, 'profesores'):
                    return redirect('teachers_applications')
                elif is_in_group(user, 'angelica'):
                    return redirect('days_validation')
                elif is_in_group(user, 'magna'):
                    return redirect('list_of_applications')
                elif is_in_group(user, 'alejandro'):
                    return redirect('list_alejandro')
                else:
                    return redirect('nothing_to_do_here')
            else:
                print("user no existe")
                return render_to_response("General/login.html", locals(), context_instance=RequestContext(request))
        else:
            print("error filling up the login form")
    else:
        form = AuthenticationForm()
    return render_to_response("General/login.html", locals(), context_instance=RequestContext(request))


def logout(request):
    auth.logout(request)
    return redirect(login)


# Not registered user (student of something..)
def nothing_to_do_here(request):
    return render_to_response("General/nothing_to_do_here.html", locals(), context_instance=RequestContext(request))


# Access denied
def access_denied(request):
    return render_to_response("General/access_denied.html", locals(), context_instance=RequestContext(request))


#Views for teachers
#Este es el formulario prototipo de financia
def financeForm(finance, newApp, id_finance_type):
    if finance.is_valid():
        try:
            checkbox = finance.cleaned_data['checkbox']
            if checkbox:
                currency = finance.cleaned_data['id_currency']
                amount = finance.cleaned_data['amount']
                type = FinanceType.objects.get(pk=id_finance_type)
                newFinance = Finance(id_application=newApp,id_finance_type=type, id_currency=currency, amount=amount)
                newFinance.save()
        except:
            print("error en financeForm method. view.py")


def destinationForm(destination, newApp):
    if destination.is_valid():
        try:
            country = destination.cleaned_data['country']
            city    = destination.cleaned_data['city']
            start_date = destination.cleaned_data['start_date']
            end_date= destination.cleaned_data['end_date']
            destiny = Destination(application=newApp,country=country, city=city, start_date=start_date, end_date=end_date)
            destiny.save()
        except:
            print("error en destinationForm method. view.py")


def documentForm(doc, newApp):
    if doc.is_valid():
        try:
            file = doc.cleaned_data['file']
            newDocument = Document(id_application = newApp, file = file)
            newDocument.save()
        except:
            file = None


def new_application(request):

    application = NewApplicationForm(request.POST or None,prefix="application")
    destinations = DestinationFormSet(request.POST or None,prefix="destinations")
    executiveReplacement = ReplacementApplicationForm(request.POST or None,prefix="executiveReplacement")
    academicReplacement = ReplacementApplicationForm(request.POST or None,prefix="academicReplacement")
    financeFormSet = FinanceFormSet(request.POST or None,prefix="finance")
    documents = DocumentFormSet(request.POST or None, request.FILES or None, prefix="documents")
    teacher_signature = TeacherSignatureForm(request.FILES or None)

    if len(request.POST) != 0:
        if application.is_valid() and destinations.is_valid() and executiveReplacement.is_valid() and academicReplacement.is_valid():
            # Applications instance
            id_teacher = Teacher.objects.get(user=request.user.id)  # TODO: ¡¡ EL PROFE ES EL PRIMERO de la LISTA cambiar por usuario del sistema !!
            ct = application.cleaned_data['id_commission_type']
            motive = application.cleaned_data['motive']
            fb = application.cleaned_data['financed_by']
            daysv = State.objects.get(pk=1)     # pendiente
            fundsv = State.objects.get(pk=1)    # pendiente

            newApp = Application(id_Teacher = id_teacher, id_commission_type = ct, motive = motive, financed_by = fb,
                                 id_days_validation_state = daysv, id_funds_validation_state = fundsv)
            newApp.save()

            #agregarle estado a la App
            #estado pendiente dcc
            state = ApplicationState.objects.get(pk=1)  # pendiente aprobacion
            stateApp = ApplicationHasApplicationState(id_application=newApp, id_application_state=state)
            stateApp.save()

            # replacement teacher information
            executiveReplace = executiveReplacement.cleaned_data['teachers']
            academicReplace = academicReplacement.cleaned_data['teachers']
            newExecutiveReplacement = Replacement(rut_teacher=executiveReplace, id_Application=newApp, id_state=daysv, type=ReplacementType.objects.get(type="Docente"))
            newAcademicReplacement  = Replacement(rut_teacher=academicReplace,  id_Application=newApp, id_state=daysv, type=ReplacementType.objects.get(type="Academico"))
            newExecutiveReplacement.save()
            newAcademicReplacement.save()

            # money
            i = 1
            for finance in financeFormSet:
                financeForm(finance, newApp, i)
                i += 1

            # destinations
            for destination in destinations:
                destinationForm(destination, newApp)

            # documents
            for document in documents:
                documentForm(document, newApp)

            # signature
            try:
                asignature = request.FILES['signature']
                id_teacher.signature.delete()
                id_teacher.signature=asignature
                id_teacher.save()
            except:
                asignature=None

            messages.success(request, 'Solicitud enviada exitosamente!')
            return redirect(teachers_applications)

        else:
            messages.error(request, 'Error en el envío del formulario.')

    return render_to_response("Professor/new_application_form.html", locals(), context_instance=RequestContext(request))

@login_required
def teacher_calendar(request):
    teacher = Teacher.objects.filter(user=request.user.id)  # me huele que es mejor usar 'get(rut=rut)', lo dejaré como 'filter' por ahora, para que no falle con bd vacía. idem para teachers_applications
    return render_to_response("Professor/teacher_calendar.html", locals(), context_instance=RequestContext(request))


@login_required
def teachers_applications(request):
    id_Teacher = Teacher.objects.filter(user=request.user.id)
    apps = Application.objects.filter(id_Teacher=id_Teacher).order_by('creation_date').reverse()
    return render_to_response("Professor/teachers_applications.html", locals(), context_instance=RequestContext(request))


@login_required
def replacement_list(request):
    teacher= Teacher.objects.filter(user=request.user.id)
    replacements = Replacement.objects.filter(rut_teacher=teacher)
    print(teacher)
    print(replacements)
    return render_to_response("Professor/replacement_list.html", locals(), context_instance=RequestContext(request))

#todo: bloquear obtencion de id que no pertenece a usuario CON UN TEST?
@login_required
def replacement_requests(request):
    replacement = Replacement.objects.get( pk = request.GET['id'] )

    if 'accept_button' in request.POST:
        replacement.id_state = State.objects.get(pk=2)
        replacement.save()
        return redirect('replacement_list')

    if 'reject_button' in request.POST:
        replacement.id_state = State.objects.get(pk=3)
        replacement.save()
        return redirect('replacement_list')

    return render_to_response("Professor/replacement_requests.html", locals(), context_instance=RequestContext(request))


def application_detail(request):
    id_app = request.GET['id']
    query = Application.objects.get(pk = id_app)
    profesor = query.id_Teacher
    sessions_rut = profesor.rut     # todo: cambiar esta variable para que calse con el rut del usuario de session!!
    comm_type = query.id_commission_type
    dest = Destination.objects.filter(application = query.id)
    replacements = query.get_replacements

    if (profesor.rut != sessions_rut):
        return redirect(access_denied)

    return render_to_response("Professor/application_detail.html", locals(), context_instance=RequestContext(request))


# Views for administrative people
def list_of_applications(request):
    apps = Application.objects.all()
    return render_to_response("Magna/list_of_applications.html", locals(), context_instance=RequestContext(request))


def application_review(request):
    id_app = request.GET['id']
    app = Application.objects.get(pk = id_app)
    profesor = app.id_Teacher
    comm_type = app.id_commission_type
    dest = Destination.objects.filter(application = app.id)
    replacements = app.get_replacements

    if len(request.POST) != 0:
        if 'accept_button' in request.POST:
            id_state = 2    # pendiente dcc
        if 'reject_button' in request.POST:
            id_state = 4    # rechazado

        state = ApplicationState.objects.get(pk = id_state)
        stateApp = ApplicationHasApplicationState(id_application = app, id_application_state=state)
        stateApp.save()
        return redirect("list_of_applications")

    return render_to_response("Magna/application_review.html", locals(), context_instance=RequestContext(request))


def historic_calendar(request):
    return render_to_response("Magna/historic_calendar.html", locals(), content_type=RequestContext(request))


# Views Alejandro
def list_alejandro(request):
    apps = Application.objects.all()
    return render_to_response("Alejandro/list_alejandro.html", locals(), context_instance=RequestContext(request))


def detail_alejandro(request):
    id_app = request.GET['id']
    application = Application.objects.get(pk = id_app)
    destinations = Destination.objects.filter(application = id_app)
    teacher = application.id_Teacher
    finances=Finance.objects.filter(id_application=id_app)
    return render_to_response("Alejandro/detail_alejandro.html", locals(), content_type=RequestContext(request))


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


# debuging views
def list(request):
    apps = Application.objects.all()
    for app in apps:
        print(app.get_state())
    return render_to_response("Magna/list.html", locals(), context_instance=RequestContext(request))
