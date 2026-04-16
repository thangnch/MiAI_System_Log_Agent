# kbAgent.py

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from agentState import AgentState

def _setup_knowledge_base():
    """Khởi tạo vector DB nội bộ"""
    knowledge_data = [
        "Error 'connection refused' is usually caused by Nginx or backend services not running. Fix: sudo systemctl restart nginx",
        "Error 'out of memory' requires checking swap or clearing logs. Fix: sudo rm -rf /var/log/*.gz",
        "If network interface is down or 'eth0' issues occur, use: sudo ip link set dev eth0 up",
        "Disk full error on /var partition: execute sudo apt-get clean",
        "High CPU usage by zombie processes. Fix: ps -ef | grep defunct | awk '{print $3}' | xargs kill -9",
        "SSH service not responding. Fix: sudo systemctl restart ssh",
        "Permission denied on web directory /var/www/html. Fix: sudo chown -R www-data:www-data /var/www/html",
        "MySQL/MariaDB 'Too many connections' error. Fix: sudo mysql -e 'SET GLOBAL max_connections = 500;'",
        "Docker container failed to start due to port conflict. Fix: sudo docker-compose down && sudo docker-compose up -d",
        "DNS resolution failure (cannot resolve host). Fix: echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf",
        "Redis server memory limit reached. Fix: redis-cli flushall",
        "System time out of sync (NTP issues). Fix: sudo timedatectl set-ntp true",
        "UFW firewall blocking port 80/443. Fix: sudo ufw allow proto tcp from any to any port 80,443",
        "Python application 'ModuleNotFoundError' in production. Fix: pip install -r requirements.txt",
        "Java application Heap Space error. Fix: update JAVA_OPTS to -Xmx2g in environment variables",
        "Broken APT packages prevent installation. Fix: sudo apt --fix-broken install",
        "Crontab jobs not executing. Fix: sudo systemctl restart cron",
        "Journald logs consuming too much space. Fix: sudo journalctl --vacuum-time=2d",
        "MongoDB failed to start due to locked file. Fix: sudo rm /var/lib/mongodb/mongod.lock && sudo systemctl start mongodb",
        "High Load Average due to I/O wait. Fix: iostat -x 1 10 to identify disk and notify admin",
        "Supervisor process entered FATAL state. Fix: sudo supervisorctl reread && sudo supervisorctl update && sudo supervisorctl restart all",
        "SSL Certificate expired on Nginx. Fix: sudo certbot renew --nginx",
        "Node.js process port already in use. Fix: sudo fuser -k 3000/tcp",
        "Swap space full causing lag. Fix: sudo swapoff -a && sudo swapon -a",
        "System clock drift or unsynchronized time causing SSL/JWT errors (certificate not yet valid, token not yet valid, clock skew). Fix: sudo timedatectl set-ntp true"
    ]

    documents = [Document(page_content=text) for text in knowledge_data]

    text_splitter = CharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=0
    )
    docs = text_splitter.split_documents(documents)

    return Chroma.from_documents(
        documents=docs,
        embedding=OpenAIEmbeddings(),
        collection_name="system_runbooks"
    )


class KBAgent:
    """KB Agent: Truy vấn giải pháp từ RAG."""

    def __init__(self, llm):
        """
        :param llm: LLM instance (phải có method invoke)
        """
        self.llm = llm
        self.vector_db = _setup_knowledge_base()

    # --- RAG ---
    def retrieve_context(self, query: str, k: int = 2) -> str:
        docs = self.vector_db.similarity_search(query, k=k)
        return "\n".join([doc.page_content for doc in docs])

    def generate_solution(self, query: str, context: str) -> str:
        prompt = f"""As a Senior SysAdmin, based on this knowledge:
        {context}
        
        What is the exact fix for this error: {query}
        Only provide the technical solution, bash command base on above knowledge. Not base on external information. 
        If can not find solution, response FAIL."""

        print("\n🚩Prompt input:", prompt)

        response = self.llm.invoke(prompt)
        print("\n🤖[KB Agent] Response:", response.content)

        return response.content

    # --- MAIN NODE ---
    def run(self, state: AgentState) -> dict:
        print("\n🤖[KB Agent] Step 2: Searching Knowledge Base for solutions...", "-" * 30)

        query = state.get("logs", "")[-1000:]
        context = self.retrieve_context(query)

        solution = self.generate_solution(query, context)

        print("\n🤖[KB Agent] Finish Step 2: Searching Knowledge Base for solutions...", "-" * 30)

        if "FAIL" in solution.upper():
            return {"kb_solution": "FAIL"}
        else:
            return {"kb_solution": solution}