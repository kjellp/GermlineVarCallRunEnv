#! /bin/env python

import os
import sys
import argparse
import subprocess



#--- Args ---

parser = argparse.ArgumentParser(description="Docker Workflow wrapper")
parser.add_argument("-i", "--input_folder",     type=str, required=True, help="Path of the input  folder")
parser.add_argument("-o", "--output_folder",    type=str, required=True, help="Path of the output folder")
parser.add_argument("-p", "--preprocessing",    action='store_true', required=False, default=False, help="Run the preprocessing   part of the workflow")
parser.add_argument("-v", "--variantcalling",   action='store_true', required=False, default=False, help="Run the variant calling part of the workflow")


args = parser.parse_args()


#--- Functions ---

def get_project_path():
  path = os.getenv("HOME")
  path = os.path.normpath(path)
  pathArray = path.split(os.sep)
  return("/{0}/{1}/".format(pathArray[1],pathArray[2]))


def get_path_from_project(path):
  path = os.path.normpath(path)
  pathArray = path.split(os.sep)
  if "/{0}/{1}/".format(pathArray[1],pathArray[2]) == get_project_path():
    del pathArray[0]
    del pathArray[0]
    del pathArray[0]
    return "/".join(pathArray)
  else:
    print("path {0} need to be absolute and in your project area : {1}").format(path, get_project_path())
    exit()


def run_workflow(docker_command):
  process = subprocess.Popen(docker_command, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  while process.poll() is None:
    out = process.stdout.read(1)
    sys.stdout.write(out.decode('utf-8'))
    sys.stdout.flush()


def run_debug(command):
  print("Command :")
  print(command)
  print("")


def test_path(path):
  if os.path.isdir(path):
    return(True)
  else:
    print("Path {0} not found".format(path))
    exit()


def test_file(path):
  if os.path.isfile(path):
    return(True)
  else:
    print("Path {0} not found".format(path))
    exit()


def is_absolute(path):
  if os.path.isabs(path):
    return(True)
  else:
    print("Path {0} is not absolute".format(path))
    exit()


def get_uid():
  process = subprocess.Popen('id -u'.split(), stdout=subprocess.PIPE)
  output, error = process.communicate()
  return output.strip()


def get_gid():
  process = subprocess.Popen('id -g'.split(), stdout=subprocess.PIPE)
  output, error = process.communicate()
  return output.strip()


def build_docker_command(input_d, output_d, reference_d, yaml_f, cust_env, user_id, project_d, container_id):
  #--- Build the command running inside the container ---
  command         = "\
  ln -s /mnt/{0} /tmp/output && \
  ln -s /mnt/{1} /tmp/input && \
  ln -s /mnt/{2} /tmp/references && \
  cd /tmp/ && \
  rbFlow.rb -r -c /mnt/{3} \
  ".format(output_d, input_d, reference_d, yaml_f)
  #--- Start the Container ---
  docker_command  = "\
  docker run -t --rm {0} {1} -v={2}:/mnt -w=/tmp {3} sh -c \"{4}\" \
  ".format(cust_env, user_id, project_d, container_id, command)
  return(docker_command)


#--- Config ---

container_id    = 'kjellptrsn/germlinevarcalldocker:latest'

user_id           = get_uid()
group_id          = '2892' # p172-member-group
custom_user_id    = "-u={0}:{1}".format(user_id,group_id)
custom_env        = '-e HOME=/tmp'

input_path        = get_path_from_project(args.input_folder)
output_path       = get_path_from_project(args.output_folder)

reference_folder  = get_path_from_project('/tsd/p172/data/durable/varcall-workflow-testing/Germline-varcall-wf-reference-files-v2.8')
prepros_yaml_file = get_path_from_project('/tsd/p172/data/durable/varcall-workflow-testing/GermlineVarCallRunEnv/preprocessing.yaml')
calling_yaml_file = get_path_from_project('/tsd/p172/data/durable/varcall-workflow-testing/GermlineVarCallRunEnv/germline_varcall.yaml')

preprocessing_wf  = args.preprocessing
variantcalling_wf = args.variantcalling
project_path      = get_project_path()



#--- Test if path are valid ---

#--- convert path to absolute ---

input_path     = os.path.abspath(input_path)
output_path    = os.path.abspath(output_path)
test_path(args.input_folder)
test_path(args.output_folder)



# Docker command

docker_prepros = build_docker_command(input_path, output_path, reference_folder, prepros_yaml_file, custom_env, custom_user_id, project_path, container_id)
docker_varcall = build_docker_command(input_path, output_path, reference_folder, calling_yaml_file, custom_env, custom_user_id, project_path, container_id)


#--- Run ---

if (preprocessing_wf == False) and (variantcalling_wf == False) :
  print('Preprocessing or Variant calling needs to be selected\n  Use -p option for Preprocessing\n  Use -v option for variant calling\n  Use -p -v to run both of them')

if preprocessing_wf :
  #run_debug(docker_prepros)
  run_workflow(docker_prepros)

if variantcalling_wf :
  #run_debug(docker_varcall)
  run_workflow(docker_varcall)

