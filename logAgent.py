# logAgent.py

import subprocess
from agentState import AgentState

class LogAgent:
    """Log Agent: Phân tích log hệ thống."""

    def __init__(self, llm, log_file: str):
        """
        :param llm: LLM instance (phải có method invoke)
        :param log_file: Đường dẫn file log
        """
        self.llm = llm
        self.log_file = log_file

    def read_logs(self, num_lines: int = 100) -> str:
        """Đọc log từ file hệ thống"""
        try:
            result = subprocess.run(
                ['tail', '-n', str(num_lines), self.log_file],
                capture_output=True,
                text=True
            )
            return result.stdout if result.stdout else "No logs found or permission denied."
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    def analyze_logs(self, logs: str) -> bool:
        """Gửi log lên LLM để phân tích"""
        print("\n🚩Log input:", logs[:100])

        prompt = f"""You are an system log investigator. Analyze these system logs content. Respond ONLY with 'YES' (if error) or 'NO'. Logs content:\n {logs[-1000:]}"""
        print("\n🚩Prompt input:", prompt[:100])

        response = self.llm.invoke(prompt)
        print("\n✅Log Analysis Response: Err = ", response.content)

        return "YES" in response.content.upper()

    def run(self, state: AgentState) -> dict:
        """Main execution method (thay cho function cũ)"""
        print("\n🤖[Log Agent] Step 1: Reading and analyzing logs...", "-" * 30)

        logs = self.read_logs()
        error_found = self.analyze_logs(logs)

        print("\n🤖[Log Agent] Finish Step 1: Reading and analyzing logs...", "-" * 30)

        return {
            "logs": logs,
            "error_found": error_found,
            "iteration": state.get("iteration", 0) + 1
        }