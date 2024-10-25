#!/bin/sh

datamodel-codegen --input-file-type jsonschema --url https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json --output-model-type pydantic_v2.BaseModel --use-union-operator --use-generic-container-types --collapse-root-models --output minecraft_docker_manager_lib/docker/compose_models.py

# Remove replace constr with str and conint with int
# Remove conint and constr from imports
sed -i -E 's/constr\([^)]*\)/str/g; s/conint\([^)]*\)/int/g; s/, conint//g; s/, constr//g' minecraft_docker_manager_lib/docker/compose_models.py