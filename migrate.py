#!/usr/bin/python3
import sys
import lib.migrate as migrate


if len(sys.argv) < 2:
    print("Usage example : ./migrate.py [PROJECT_IDENTIFIER]")
    sys.exit(1)

project_identifier = sys.argv[-1]

try:
    success = migrate.run(project_identifier)
except Exception as e:
    print("something gone wrong ({0})".format(e))

if not success:
    print("Project with identifier '{0}' not found on src database".format(
        project_identifier
    ))
    sys.exit(1)

print("all tasks finished successfully.")
