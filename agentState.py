# agentState.py

from typing import TypedDict


class AgentState(TypedDict):
    """
    Shared state giữa các agents trong workflow
    """

    logs: str                 # Nội dung log đã đọc
    error_found: bool         # Có phát hiện lỗi hay không
    kb_solution: str          # Giải pháp từ knowledge base
    iteration: int            # Số lần lặp workflow
    is_fixed: bool            # Lỗi đã được fix hay chưa