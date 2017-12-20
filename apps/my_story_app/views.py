from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Prefetch
from rest_framework.decorators import api_view

from common.views import *
from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry, PatientController
from emr.operations import op_add_event
from users_app.views import permissions_accessed
from .serializers import MyStoryTextComponentEntrySerializer, MyStoryTextComponentSerializer, MyStoryTabSerializer


@login_required
def track_tab_click(request):
    resp = {'success': False}
    if request.POST.get("tab_id", None):
        tab_info = MyStoryTab.objects.get(id=request.POST.get("tab_id", None))
        if permissions_accessed(request.user, tab_info.patient.id):
            actor = request.user
            patient = tab_info.patient

            summary = "<b>%s</b> accessed %s" % (actor.username, tab_info.name)
            op_add_event(actor, patient, summary)
            resp['success'] = True

    return ajax_response(resp)


@login_required
@timeit
def get_my_story(request, patient_id):
    resp = {'success': False}

    # Medication staff(s) created tab
    # -> All patient
    # -> Only this patient

    # Patient's created tab
    # -> Public
    # -> Private

    # How we load the tab's component
    # All tabs belong this this patient and public
    # At first the tabs result must be belong to request patient
    # TODO:
    # tabSet = MyStoryTab.objects.filter(patient_id=int(patient_id))
    # TODO: List of all medication staff whose control this patient -> Get a list of tab's author may shared tabs for me
    # staff = PatientController.objects.filter(patient_id = int(patient_id)).get()
    # tabSet2 = MyStoryTab.object.filter(author_id__in=staff).filter(is_all=True) = .filter(Q(condition_1) & Q(condition_2))
    # TODO: If request user is not a patient the filtered about
    # tabSet2.filter(private = False)
    # If request user is patient himself then return all
    # If request user is physician | admin | nurse | secretary | mid-level then add privileges filters to public (a.k.a private = False)
    # ---> Additionally new tab array which created by request user and shared between all patient (a.k.a is_all = True) and
    if permissions_accessed(request.user, int(patient_id)):
        # # METHOD 2: NEW WAY
        staffIDList = PatientController.objects.filter(patient_id=int(patient_id)).values_list('physician_id',
                                                                                               flat=True)

        myStoryTabComponentQuerySet = MyStoryTextComponent.objects.filter(
            Q(patient_id=int(patient_id)) | (Q(author_id__in=staffIDList) & Q(is_all=True)))
        if request.user.profile.role != 'patient':
            myStoryTabComponentQuerySet = myStoryTabComponentQuerySet.filter(private=False)

        myStoryTabQuerySet = MyStoryTab.objects.prefetch_related(
            Prefetch('my_story_tab_components', queryset=myStoryTabComponentQuerySet),
            'my_story_tab_components__text_component_entries').filter(
            Q(patient_id=int(patient_id)) | (Q(author_id__in=staffIDList) & Q(is_all=True)))
        if request.user.profile.role != 'patient':
            myStoryTabQuerySet = myStoryTabQuerySet.filter(private=False)

        # # METHOD 1: OLD WAY
        # # Load all tab belong to this patient OR it being shared between all patients
        # myStoryTabQuerySet = MyStoryTab.objects.filter(Q(patient_id=int(patient_id)) | Q(is_all=True))
        # myStoryTabQuerySet.filter()
        # # Then filter tab result above by tab's author (7, 8, 9 : probably the second condition is_all = True)
        # # If patient is not under control by tab's author
        # # TODO: Caveats doing this filtering in python is much more expensive than tradition SQL query
        # # Should moving out the author filter above
        # exclude_tabs = []
        # for tab in myStoryTabQuerySet:  # Hit DB
        #     if tab.author.profile.role == 'physician' and tab.is_all:
        #         patient_controllers = PatientController.objects.filter(physician=tab.author)  # Hit DB
        #         patient_ids = [x.patient.id for x in
        #                        patient_controllers]  # x.patient.id also have lower performance than x.patient_id
        #
        #         if not int(patient_id) in patient_ids:
        #             exclude_tabs.append(tab.id)
        #
        # myStoryTabQuerySet = myStoryTabQuerySet.exclude(id__in=exclude_tabs)
        #
        # resp['success'] = True
        # tabs_serializer = MyStoryTabSerializer(myStoryTabQuerySet, many=True).data
        #
        # # Load tab's component(Apply filtering as my tab above) and component entries
        # for tab in tabs_serializer:
        #     components = MyStoryTextComponent.objects.filter(tab_id=tab["id"]).filter(Q(patient_id=int(patient_id)) | Q(is_all=True))
        #     exclude_components = []
        #     for component in components:
        #         if component.author.profile.role == 'physician' and component.is_all:
        #             patient_controllers = PatientController.objects.filter(physician=component.author)
        #             patient_ids = [x.patient.id for x in patient_controllers]
        #
        #             if not int(patient_id) in patient_ids:
        #                 exclude_components.append(component.id)
        #
        #     components = components.exclude(id__in=exclude_components)
        #
        #     tab["my_story_tab_components"] = MyStoryTextComponentSerializer(components, many=True).data
        #     for component in tab["my_story_tab_components"]:
        #         entries = MyStoryTextComponentEntry.objects.filter(component_id=component["id"], patient_id=int(patient_id))
        #         component["text_component_entries"] = MyStoryTextComponentEntrySerializer(entries, many=True).data

        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(myStoryTabQuerySet, many=True).data
    return ajax_response(resp)


@login_required
def get_tab_info(request, tab_id):
    resp = {'success': False}
    tab_info = MyStoryTab.objects.get(id=tab_id)
    if permissions_accessed(request.user, tab_info.patient.id):
        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(tab_info).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def add_tab(request, patient_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        all_patients = True if request.POST.get('all_patients', False) else False

        tab = MyStoryTab.objects.create(patient_id=int(patient_id),
                                        author=request.user,
                                        name=request.POST.get("name", None))

        private = True if request.POST.get('private', False) else False
        tab.private = private
        if all_patients:
            tab.is_all = True
        tab.save()

        resp['tab'] = MyStoryTabSerializer(tab).data
        resp['tab']["my_story_tab_components"] = []
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def add_text(request, patient_id, tab_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        patient_user = User.objects.get(id=patient_id)

        all_patients = True if request.POST.get('all_patients', False) else False
        text = MyStoryTextComponent()
        text.name = request.POST.get("name", None)
        text.concept_id = request.POST.get("concept_id", None)

        private = True if request.POST.get('private', False) else False
        text.private = private

        text.patient = patient_user
        text.author = request.user
        text.tab = tab

        if all_patients and tab.is_all:
            text.is_all = True
        text.save()

        entry = MyStoryTextComponentEntry()
        entry.component = text
        entry.text = request.POST.get("text", None)
        entry.patient = patient_user
        entry.author = request.user
        entry.save()

        if text:
            resp['component'] = MyStoryTextComponentSerializer(text).data
            entries = MyStoryTextComponentEntry.objects.filter(component_id=text.id, patient_id=int(patient_id))
            resp['component']["text_component_entries"] = MyStoryTextComponentEntrySerializer(entries, many=True).data
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def delete_tab(request, patient_id, tab_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        if request.user.id == tab.author.id:
            MyStoryTextComponentEntry.objects.filter(component__tab=tab).delete()
            MyStoryTextComponent.objects.filter(tab=tab).delete()
            tab.delete()
        
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def save_tab(request, patient_id, tab_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.get(id=int(tab_id))
        if request.user.id == tab.author.id:
            tab.name = request.POST.get("name", None)
            tab.save()
            
            resp['tab'] = MyStoryTabSerializer(tab).data
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def delete_text_component(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = MyStoryTextComponent.objects.get(id=int(component_id))
        if request.user.id == component.author.id:
            MyStoryTextComponentEntry.objects.filter(component=component).delete()
            component.delete()
        
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["save_text_component"])
def save_text_component(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = MyStoryTextComponent.objects.get(id=int(component_id))
        if request.user.id == component.author.id:
            component.name = request.POST.get("name", None)
            component.concept_id = request.POST.get("concept_id", None)

        component.save()
        
        resp['component'] = MyStoryTextComponentSerializer(component).data
        entries = MyStoryTextComponentEntry.objects.filter(component_id=component.id, patient_id=int(patient_id))
        resp['component']["text_component_entries"] = MyStoryTextComponentEntrySerializer(entries, many=True).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
@permissions_required(["save_text_component"])
def save_text_component_entry(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = MyStoryTextComponent.objects.get(id=int(component_id))
        patient = User.objects.get(id=patient_id)

        entry = MyStoryTextComponentEntry()
        entry.component = component
        entry.text = request.POST.get("text", None)
        entry.patient = patient
        entry.author = request.user
        entry.save()

        resp['entry'] = MyStoryTextComponentEntrySerializer(entry).data

        actor = request.user

        summary = "<b>%s</b> note was updated to %s" % (component.name, entry.text)
        op_add_event(actor, patient, summary)

        resp['success'] = True

    return ajax_response(resp)