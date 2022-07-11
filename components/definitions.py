from pathlib import Path
from string import Template

from kfp import components

import subprocess

DEFINITIONS_FOLDER = Path(__file__).absolute().parent
CURRENT_GIT_HASH = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],cwd=str(DEFINITIONS_FOLDER)).decode('utf-8').strip()

def load_component(component_path: Path) -> str:
    """
    Loads a component definition from YAML file.
    Substitutes the current git hash into the component definition.

    :params component_path: Path to the component definition file.
    """
    
    with component_path.open() as inp:
        component_definition = Template(inp.read())
        component_definition = component_definition.substitute({'CURRENT_GIT_HASH': CURRENT_GIT_HASH})
        return components.load_component(text = component_definition)
download_file_from_s3_step = load_component(DEFINITIONS_FOLDER / 'download_file_from_s3.yaml')

train_classifier_step = load_component(DEFINITIONS_FOLDER / 'train_classifier.yaml')
