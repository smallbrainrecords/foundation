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
from emr.models import ObservationValue, UserProfile, SharingPatient, PatientController, PhysicianTeam


@timeit
def get_vitals_table_component(patient_id, component_name):
    return ObservationValue.objects.filter(component__name=component_name).filter(
        component__observation__subject_id=patient_id).order_by(
        '-effective_datetime')[0:5]


@timeit
def permissions_accessed(user, obj_user_id):
    """
    Check whether or not clinical staff(s) can control patient
    :param user: Clinical staff
    :param obj_user_id: Patient
    :return:
    """
    permitted = False

    user_profile = UserProfile.objects.get(user=user)
    if user_profile.role == 'admin':
        permitted = True

    elif user_profile.role == 'patient':
        if user.id == obj_user_id:
            permitted = True
        sharing_patients = SharingPatient.objects.filter(shared_id=obj_user_id)
        patient_ids = [x.sharing.id for x in sharing_patients]
        if user.id in patient_ids:
            permitted = True

    elif user_profile.role == 'physician':
        patient_controllers = PatientController.objects.filter(physician=user)
        patient_ids = [x.patient.id for x in patient_controllers]
        patient_ids.append(user.id)
        if obj_user_id in patient_ids:
            permitted = True

    elif user_profile.role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=user)
        physician_ids = [x.physician.id for x in team_members]
        patient_controllers = PatientController.objects.filter(physician__id__in=physician_ids)
        patient_ids = [x.patient.id for x in patient_controllers]
        patient_ids.append(user.id)
        if obj_user_id in patient_ids:
            permitted = True

    return permitted


@timeit
def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False