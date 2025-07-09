def format_transport_subtype(transport_subtype):
    if not transport_subtype:
        return transport_subtype

    first_alpha_index = next((i for i, ch in enumerate(transport_subtype) if ch.isalpha()), None)

    if first_alpha_index is None:
        return transport_subtype

    if transport_subtype[first_alpha_index].isupper():
        return transport_subtype

    if first_alpha_index == 0:
        return transport_subtype.capitalize()

    return (
        transport_subtype[:first_alpha_index]
        + transport_subtype[first_alpha_index].upper()
        + transport_subtype[first_alpha_index + 1:]
    )

