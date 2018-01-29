from emr.models import ObservationValue


def get_observation_most_common_value(component, effective_datetime):
    """
    Get most recent value of observation component
    :param component:
    :param effective_datetime:
    :return: 
    """
    observation_component = ObservationValue.objects.filter(component=component).filter(
        effective_datetime=effective_datetime)

    if observation_component.exists():
        return float(observation_component.first().value_quantity)
    else:
        most_recent_value = ObservationValue.objects.filter(component=component).order_by('-effective_datetime')
        if most_recent_value.exists():
            return float(most_recent_value.first().value_quantity)
        else:
            return float(1)
