# actionAgent.py

import time
import subprocess
from agentState import AgentState

class ResolveAgent:
    """Resolve Agent: Thực thi lệnh bash từ solution."""

    def __init__(self, llm, execute: bool = False, delay: int = 5):
        """
        :param llm: LLM instance (phải có method invoke)
        :param execute: Có thực thi thật bash command hay không (default: False để an toàn)
        :param delay: Thời gian sleep giữa các lệnh (giây)
        """
        self.llm = llm
        self.execute = execute
        self.delay = delay

    def generate_commands(self, solution: str) -> list:
        """Convert solution → bash commands"""
        prompt = f"""Convert this solution into a sequence of executable Ubuntu bash commands:
        '{solution}'
        Return ONLY the commands, one per line. No explanation, no markdown blocks."""

        response = self.llm.invoke(prompt)
        print("\n🤖[Resolve Agent] Raw command response:", response.content)

        commands = response.content.strip().split('\n')
        return [cmd.strip() for cmd in commands if cmd.strip()]

    def execute_commands(self, commands: list):
        """Thực thi các command"""
        for cmd in commands:
            print(f"   >> Executing: {cmd}")
            print("😴 Sleeping for viewing...\n")
            time.sleep(self.delay)

            if self.execute:
                try:
                    subprocess.run(cmd, shell=True, check=True)
                except Exception as e:
                    print(f"❌ Error executing command: {e}")

    def run(self, state: AgentState) -> dict:
        """Main execution method (LangGraph node)"""
        print("\n🤖[Resolve Agent] Step 3: Translating solution to bash and executing...", "-" * 30)

        solution = state.get("kb_solution", "")

        # Nếu không có solution thì skip
        if not solution or solution.upper() == "FAIL":
            print("⚠️ No valid solution found. Skipping execution.")
            return {"is_fixed": False}

        commands = self.generate_commands(solution)
        self.execute_commands(commands)

        print("\n🤖[Resolve Agent] Finish Step 3: Translating solution to bash and executing...", "-" * 30)

        return {"is_fixed": True}