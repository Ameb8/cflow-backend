import subprocess
import tempfile
import os

from file_sys_app.models import Folder, File

CONTAINER_ROOT_PATH = "/deploy"
OUTPUT_BINARY_PATH = "/deploy/a.out"


def start_docker(container_name):
    cmd = [
        "docker", "run", "-d", "--rm",
        "--name", container_name,
        "--cpus=0.5", "--memory=256m", "--pids-limit=64",
        "--network", "none",
        "gcc:latest", "sleep", "30"
    ]
    subprocess.run(cmd, check=True)

def to_docker(container_name, source_path, destination_path):
    subprocess.run(["docker", "cp", source_path, f"{container_name}:{destination_path}"], check=True)

def clean_docker(container_name):
    subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL)

def start_docker_exec(container_name):
    cmd = [
        "docker", "run", "-dit", "--rm",
        "--name", container_name,
        "--cpus=0.5", "--memory=256m", "--pids-limit=64",
        "--network", "none",
        "gcc:latest", "/bin/bash"
    ]
    subprocess.run(cmd, check=True)


def docker_exec(container_name, command):
    # Run a command inside the running container
    result = subprocess.run(
        ["docker", "exec", container_name] + command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout, result.stderr

def docker_create_folder(container_name, folder_path):
    # Create folder inside container using mkdir -p
    docker_exec(container_name, ["mkdir", "-p", folder_path])


def docker_move_file(container_name, folder_path, file):
    # Compose file name with extension
    file_name = file.file_name
    if file.extension:
        file_name += f".{file.extension}"

    # Write file_content to temp file
    with tempfile.NamedTemporaryFile("w", delete=False) as tmpf:
        tmpf.write(file.file_content or "")
        tmp_file_path = tmpf.name

    container_file_path = os.path.join(folder_path, file_name)
    # Copy temp file into container
    to_docker(container_name, tmp_file_path, container_file_path)

    # Remove temp file
    os.unlink(tmp_file_path)


def docker_move_folder(container_name, folder, parent_path_in_container):
    """
    Recursively moves the given folder and all its subfolders and files into the container,
    recreating the folder structure starting from parent_path_in_container.
    """
    folder_path_in_container = os.path.join(parent_path_in_container, folder.folder_name)
    docker_create_folder(container_name, folder_path_in_container)

    # Copy files in current folder
    for file in folder.files.all():
        docker_move_file(container_name, folder_path_in_container, file)

    # Recursively process subfolders
    for subfolder in folder.subfolders.all():
        docker_move_folder(container_name, subfolder, folder_path_in_container)


def docker_move_proj(container_name, root_folder):
    base_path_in_container = "/deploy"
    start_docker_exec(container_name)
    docker_create_folder(container_name, base_path_in_container)

    docker_move_folder(container_name, root_folder, base_path_in_container)

    print(f"Deployment of folder '{root_folder.folder_name}' to container '{container_name}' completed.")

def docker_compile(container_name, root_folder_path="/deploy", output_binary="/deploy/a.out"):
    compile_cmd = [
        "bash", "-c",
        f"gcc $(find {root_folder_path} -name '*.c') -o {output_binary}"
    ]

    stdout, stderr = docker_exec(container_name, compile_cmd)

    if stderr:
        print(f"Compilation errors:\n{stderr}")
    else:
        print(f"Compilation succeeded. Binary created at {output_binary}")

    return stdout, stderr

def docker_compile_proj(container_name, root_folder):
    output_binary = OUTPUT_BINARY_PATH
    base_path_in_container = CONTAINER_ROOT_PATH

    start_docker_exec(container_name) # Start container

    try:
        # Deploy project files
        docker_create_folder(container_name, base_path_in_container)
        docker_move_folder(container_name, root_folder, base_path_in_container)

        # Compile project
        stdout, stderr = docker_compile(container_name, base_path_in_container, output_binary)

        # Copy compiled executable to return
        with tempfile.NamedTemporaryFile(delete=False) as tmp_exe:
            tmp_exe_path = tmp_exe.name

        subprocess.run(["docker", "cp", f"{container_name}:{output_binary}", tmp_exe_path], check=True)

        with open(tmp_exe_path, "rb") as f:
            executable_bytes = f.read()

        os.unlink(tmp_exe_path)

    finally:
        clean_docker(container_name) # clean container

    return stdout, stderr, executable_bytes

