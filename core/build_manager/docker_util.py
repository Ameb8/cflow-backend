import subprocess

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