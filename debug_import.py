import sys

print("Python path:", sys.path)
try:
    import backend

    print("backend module imported")
    print("backend contents:", dir(backend))
except Exception as e:
    print("Error importing backend:", e)
try:
    import backend.domain

    print("backend.domain imported")
    print("backend.domain contents:", dir(backend.domain))
except Exception as e:
    print("Error importing backend.domain:", e)
try:
    from backend.domain import session_manager

    print("session_manager imported")
    print("session_manager contents:", dir(session_manager))
except Exception as e:
    print("Error importing session_manager:", e)
    import traceback

    traceback.print_exc()
