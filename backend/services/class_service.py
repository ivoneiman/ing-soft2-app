try:
    from models import Class, Enrollment
except ModuleNotFoundError:
    from ..models import Class, Enrollment


def enrollment_counts():
    counts = (
        Enrollment.query
        .with_entities(Enrollment.class_id, Enrollment.estado)
        .filter(Enrollment.estado.in_(Enrollment.CAPACITY_STATUSES))
        .all()
    )
    result = {}
    for class_id, _estado in counts:
        result[class_id] = result.get(class_id, 0) + 1
    return result


def class_slot_payload(class_obj, enrolled_count):
    duration = getattr(class_obj, "duration_minutes", 60)
    cupo_max = class_obj.cupoMaximo if class_obj.cupoMaximo is not None else 20
    clase_estado = getattr(class_obj, "estado", Class.STATUS_ACTIVE)
    if clase_estado == Class.STATUS_CANCELLED:
        available = cupo_max
        enrolled = 0
        is_full = False
    else:
        available = cupo_max - enrolled_count
        enrolled = enrolled_count
        is_full = available <= 0

    return {
        "id": class_obj.id,
        "name": class_obj.name,
        "actividad": class_obj.actividad.name if hasattr(class_obj, "actividad") and class_obj.actividad else None,
        "fecha_hora": class_obj.fecha_hora.isoformat() if class_obj.fecha_hora else None,
        "time": class_obj.fecha_hora.strftime("%H:%M") if class_obj.fecha_hora else "",
        "duration_minutes": duration,
        "cupoMaximo": cupo_max,
        "enrolled": enrolled,
        "available_spots": available,
        "is_full": is_full,
        "estado": clase_estado,
        "descuento": class_obj.descuento,
    }
