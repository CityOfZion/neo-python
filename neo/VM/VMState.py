
NONE = 0
HALT = 1 << 0
FAULT = 1 << 1
BREAK = 1 << 2


def VMStateStr(_VMState):
    if _VMState == NONE:
        return "NONE"

    state = []
    if _VMState & HALT:
        state.append("HALT")
    if _VMState & FAULT:
        state.append("FAULT")
    if _VMState & BREAK:
        state.append("BREAK")

    return ", ".join(state)
