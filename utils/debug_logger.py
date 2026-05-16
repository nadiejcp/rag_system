class DebugLogger:
    def __init__(self, enabled=False):
        self.enabled = enabled

    def log(self, phase: str, message: str, data: any = None):
        if not self.enabled:
            return

        print(f"\n🔍 DEBUG [{phase}] {message}")
        if data:
            print(f"📊 Data: {data}")
