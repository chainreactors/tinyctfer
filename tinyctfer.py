"""
TinyCTFer - A 100-line "Baby Runtime" for Intent Engineering

Authors: l3yx, m09ic

Philosophy: "Intent is All You Need" 

Meta-Tooling Innovation:
Traditional: Agent → Tool A → Parse → Tool B → Parse... (context pollution)
Ours:  Agent Intent → Write Python Code → Execute → Final Result 

Result: Top 4 in Tencent Cloud Hackathon (238 teams), only ~1500 RMB tokens (kimi k2, not deepseek)

Components: Claude Code + AI-Friendly Sandbox ( Python Executor MCP + Meta-Tooling + VNC)

References:
- https://wiki.chainreactors.red/blog/2025/12/01/intent_is_all_you_need/
- https://wiki.chainreactors.red/blog/2025/12/02/intent_engineering_01/
"""

import os
import argparse
from pathlib import Path
import docker
from docker.models.containers import Container
from docker.errors import ImageNotFound

# Script directory for mounting claude_code configuration into container
SCRIPT_DIR = Path(__file__).resolve().parent

class Ctfer:
    """CTF Solver Runtime - Provide AI maximum freedom within safe container boundary"""
    def __init__(self, vnc_port, workspace):
        # Sandbox: Ubuntu desktop + Claude Code + Python Executor MCP + Toolset + Security tools
        self.image = "l3yx/sandbox:latest"
        self.volumes = [
            f"{SCRIPT_DIR/'claude_code'}:/opt/claude_code:ro",  # Claude config (ro)
            f"{workspace}:/home/ubuntu/Workspace"  # AI's workspace (rw)
        ]
        self.environment = {  # Anthropic API credentials
            "ANTHROPIC_BASE_URL": os.getenv("ANTHROPIC_BASE_URL"),
            "ANTHROPIC_AUTH_TOKEN": os.getenv("ANTHROPIC_AUTH_TOKEN"),
            "ANTHROPIC_MODEL": os.getenv("ANTHROPIC_MODEL"),
            "NO_CODESERVER": "true"
        }
        self.ports = {f"{vnc_port}":"5901"}  # VNC for human observation
        self.docker_client = docker.DockerClient()
        self.container = None
        try:
            self.docker_client.images.get(self.image)
        except ImageNotFound:
            print(f"[-] Docker image '{self.image}' not found. Please pull it first.")
            exit(1)
        self.container:Container = self.docker_client.containers.run(
            image=self.image, volumes=self.volumes, environment=self.environment,
            ports=self.ports, detach=True, remove=True
        )

    def cleanup(self):
        if self.container:
            try:
                self.container.stop(timeout=5)
            except Exception:
                pass

    def __del__(self):
        self.cleanup()

if __name__ == "__main__":
    # Main Entry Point: The 100-line Baby Runtime in Action
    parser = argparse.ArgumentParser(description='CTF Challenge Solver')
    parser.add_argument('--ctf', type=str, required=True, help='CTF challenge URL')
    parser.add_argument('--vnc-port', type=int, default=5901, help='VNC port (default: 5901)')
    parser.add_argument('--workspace', type=str, default="workspace", help='Workspace directory (default: workspace)')

    args = parser.parse_args()
    ctf = args.ctf
    vnc_port = args.vnc_port
    workspace = os.path.abspath(args.workspace)

    task = f'''
    Use the security-ctf-agent: Solve the CTF challenge (obtaining the Flag completes the task, you can end work immediately, don't need to verify the flag's accuracy.)

    Challenge Information:
    {ctf}

    **You don't need to scan ports or IP segments, all IP and ports needed for solving are already listed**
    '''.strip()

    print("[+] 启动沙盒...")
    ctfer = Ctfer(vnc_port, workspace)
    print("[+] 等待沙盒环境和mcp服务就绪...")
    ctfer.container.exec_run(["bash","wait.sh"], workdir="/opt/claude_code")
    print("[+] mcp服务已就绪...")
    print(f"[+] 可以连接 vnc://127.0.0.1:{vnc_port} 查看可视化界面, 密码123456")
    print(f"[+] 开始解题, 可以打开 {workspace} 查看解题步骤")
    res = ctfer.container.exec_run(["claude", "--dangerously-skip-permissions", "--print", task], workdir="/opt/claude_code")
    ctfer.cleanup()
    print("[+] 结束运行")
    print(bytes.decode(res.output))