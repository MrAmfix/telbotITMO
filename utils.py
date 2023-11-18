import base


def registration(user_id: int, fullname: str):
    is_reg = base.is_registered(user_id)
    if is_reg:
        base.logging(f"[REGISTRATION]: user {user_id} rename changed name ({is_reg}) --> ({fullname})")
        base.update_fullname(user_id, fullname)
    else:
        base.logging(f"[REGISTRATION]: user {user_id} registered as ({fullname})")
        base.registration(user_id, fullname)
