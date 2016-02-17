import wtforms


def required_if(other, message=None):
    """
    Marks the current field as required if the other field is truthy

    :param other: The name of the other field in the form
    :param message: (optional) Error message to return
    """

    def validator(form, field):
        other_field = form._fields.get(other)

        if other_field is None:
            raise Exception('no field named "%s" in form' % other_field)

        if bool(other_field.data):
            wtforms.validators.input_required(message)(form, field)
        else:
            wtforms.validators.optional()(form, field)

    return validator
