# tests that repo conforms to expectations
import os
import re
from app_lib.app_paths import ROOT_DIR


class ConsistencyException(Exception):
    pass


def _get_string_from_file(
    match_object: re.Pattern,  # type: ignore
    file_path: str,
) -> str:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    target_lines = [match_object.match(i) for i in lines]
    target_lines = [i for i in target_lines if i]
    if len(target_lines) != 1:
        err_str = 'did not find unique match for {} in {}'.format(
            match_object.pattern,
            file_path,
        )
        raise ConsistencyException(err_str)
    unique_match_object = target_lines[0]
    if unique_match_object is None:
        err_str = 'expected match object for {} is None'.format(match_object)
        raise ConsistencyException(err_str)
    try:
        target_string = unique_match_object.group(1)
    except IndexError:
        err_str = 'extracting group(1) failed on {} using regex {}'.format(
            unique_match_object,
            match_object,
        )
        raise ConsistencyException(err_str)
    return target_string


##############################################
# ensure flask app names configured properly #
##############################################
SCRIPTS_FILE_PATH = os.path.join(ROOT_DIR, 'scripts.sh')

# retreive referenced module for flask server
flask_app_file_location_re = re.compile(r'^FLASK_APP_MODULE_LOCATION[]*=[]*(.*)')
try:
    referenced_module_location = _get_string_from_file(
        match_object=flask_app_file_location_re,
        file_path=SCRIPTS_FILE_PATH,
    )
except ConsistencyException:
    err_str = '{} does not have proper flask app configuration. expected unique match for {}'.format(
        SCRIPTS_FILE_PATH,
        flask_app_file_location_re.pattern,
    )
    raise ConsistencyException(err_str)
infered_python_file = '{}.py'.format(referenced_module_location)
infered_python_file_path = os.path.join(ROOT_DIR, infered_python_file)

# check if referenced module exists
if not os.path.exists(infered_python_file_path):
    err_str = '{} references flask module {}. does not exist'.format(
        SCRIPTS_FILE_PATH,
        infered_python_file,
    )
    raise ConsistencyException(err_str)

# retreive referenced flask app name
docker_flask_app_name_re = re.compile(r'^FLASK_APP_NAME_IN_CODE[ ]*=[ ]*(.*)')
try:
    referenced_flask_app_name = _get_string_from_file(
        match_object=docker_flask_app_name_re,
        file_path=SCRIPTS_FILE_PATH,
    )
except ConsistencyException:
    err_str = '{} does not have proper flask app configuration. expected unique match for {}'.format(
        SCRIPTS_FILE_PATH,
        docker_flask_app_name_re.pattern,
    )
    raise ConsistencyException(err_str)

# retreive actual flask app name
python_flask_app_name_re = re.compile(r'(.*) = Flask\(__name__\).*')
try:
    actual_flask_app_name = _get_string_from_file(
        match_object=python_flask_app_name_re,
        file_path=infered_python_file_path,
    )
except ConsistencyException:
    err_str = '{} does not have proper flask app configuration. expected unique match for {}'.format(
        infered_python_file_path,
        python_flask_app_name_re.pattern,
    )
    raise ConsistencyException(err_str)

# verify same name
if referenced_flask_app_name != actual_flask_app_name:
    err_str = 'flask app names inconsistent. Dockerfile reference: {}. Flask app name: {}.'.format(
        referenced_flask_app_name,
        actual_flask_app_name,
    )
    raise ConsistencyException(err_str)
