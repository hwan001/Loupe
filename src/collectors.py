# collectors.py
import time
import psutil
import random
import threading
from datetime import datetime

class BaseCollector:
    def __init__(self, queue, interval=5):
        self.queue = queue
        self.interval = interval
        self.is_running = False

    def collect(self):
        pass

    def run(self):
        self.is_running = True
        while self.is_running:
            try:
                data = self.collect()
                if data:
                    self.queue.put(data)
            except Exception as e:
                print(f"❌ {self.__class__.__name__} 오류: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False

# ---------------------------------------------------------
# 1. [System] 실제 서버 메트릭 수집기 (최적화됨)
# ---------------------------------------------------------
class SystemMetricCollector(BaseCollector):
    def __init__(self, queue, interval=10):
        super().__init__(queue, interval)
        self.last_cpu = 0  # 이전 CPU 값 저장용

    def collect(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # [최적화] 이전 값과 차이가 5% 미만이고, 80% 미만의 안정 상태면 기록 생략
        if abs(cpu_usage - self.last_cpu) < 5 and cpu_usage < 80:
            return None 

        self.last_cpu = cpu_usage

        if cpu_usage > 50:
            level = "CRITICAL" 
            msg = f"CPU 사용량이 {cpu_usage}%로 매우 높습니다. 시스템 과부하가 우려됩니다."
        else:
            level = "NORMAL"
            msg = f"현재 CPU 사용량은 {cpu_usage}%, 메모리 사용량은 {memory.percent}%로 안정적입니다."

        timestamp = datetime.now().strftime("%H:%M:%S")
        return ("SYSTEM", f"[{timestamp}] [Metric-{level}] {msg}")

# ---------------------------------------------------------
# 2. [Finance] (기존 동일)
# ---------------------------------------------------------
class FinanceCollector(BaseCollector):
    def collect(self):
        if random.random() > 0.3: return None
        items = ["스타벅스 커피", "AWS 서버 비용", "택시비", "편의점 야식", "GPT-4 구독료"]
        amounts = [5000, 150000, 12000, 8000, 22000]
        idx = random.randint(0, len(items)-1)
        timestamp = datetime.now().strftime("%H:%M:%S")
        return ("FINANCE", f"[{timestamp}] [Card] '{items[idx]}' 결제로 {amounts[idx]}원이 출금되었습니다.")

# ---------------------------------------------------------
# 3. [Log] (기존 동일)
# ---------------------------------------------------------
class AppLogCollector(BaseCollector):
    def collect(self):
        if random.random() > 0.4: return None
        events = [
            "사용자 'admin'이 로그인에 성공했습니다.",
            "DB 연결 풀(Connection Pool)이 가득 찼습니다.",
            "API 요청 응답 시간이 2000ms를 초과했습니다 (Slow Query).",
            "백그라운드 배치 작업이 완료되었습니다."
        ]
        timestamp = datetime.now().strftime("%H:%M:%S")
        event = random.choice(events)
        tag = "ERROR" if "초과" in event or "가득" in event else "INFO"
        return ("APP_LOG", f"[{timestamp}] [Log-{tag}] {event}")